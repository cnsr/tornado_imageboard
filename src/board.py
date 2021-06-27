# -*- coding: utf-8 -*-
import html
import datetime
import json
import logging
import os
import random
import re
from mimetypes import guess_type
from uuid import uuid4
from typing import Optional

import geoip2.database as gdb
import motor.motor_tornado
import pymongo
import tornado.autoreload
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from PIL import Image
from tornado import concurrent, gen
from tornado.options import define, options

import src.ib_settings as default_settings
import src.uimodules as uimodules
from src.admin import (
    AdminLoginHandler, AdminLogoutHandler,
    AdminStatsHandler, AdminBannedHandler, AdminReportsHandler,
    AdminHandler, AdminBoardCreationHandler, AdminBoardEditHandler,
    AdminLogsHandler, AdminBlackListHandler, AdminIPSearchHandler,
)
from src.ajax import *
from src.api import *
from src.getresolution import resolution
from src.logger import log
from src.thumbnail import make_thumbnail
from src.tripcode import tripcode
from src.utils import *
from src.userhandle import UserHandler, ProfilePage

define('port', default=default_settings.PORT, help='run on given port', type=int)

logger = logging.getLogger('board')
logger.setLevel(logging.DEBUG)
# console log handler
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
logger.addHandler(ch)

executor = concurrent.futures.ThreadPoolExecutor(8)

uploads = default_settings.UPLOAD_ROOT

# TODO: rewrite this atrocity
global latest_postnumber
latest_postnumber = 0

regioncodes = RegionCodes()

gdbr = gdb.Reader(os.path.join('static', 'GeoLite2-City.mmdb'))


# this is done to ensure user does not input any html in posting form
def strip_tags(inbound_html: str) -> str:
    # MLStripper fucks up posts with more than one "<"
    tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
    no_tags = tag_re.sub('', inbound_html)
    return html.escape(no_tags)


async def roll(subject: str) -> Optional[str]:
    matches = re.compile(r'r(oll)? ([1-9])d([1-9]$|[1-9][0-9]{0,3}$)').match(subject)
    if not matches:
        return None
    count = int(matches.group(2))
    sides = int(matches.group(3))
    return f"Rolled {', '.join(str(random.randint(0, sides)) for i in range(count))}"


# list of boards
class IndexHandler(UserHandler):

    async def get(self):
        await self.render('index.html', boards=await self.boards)


# map of posters
class MapHandler(UserHandler):

    async def get(self):
        await self.render('map.html', boards=await self.boards)


# list of threads
class BoardHandler(UserHandler):

    async def get(self, board):
        db = self.database
        # TODO: add class for board
        db_board = await db.boards.find_one({'short': board})
        if db_board:
            banner = None
            if db_board['banners']:
                banner = random.choice(db_board['banners'])
            threads = await db.posts.find(
                {'board': board, 'oppost': True}
            ).sort(
                [('pinned', -1), ('lastpost', -1)]
            ).limit(db_board['thread_catalog']).to_list(None)

            for thread in threads:
                limit = 1 if thread['pinned'] else 3
                posts = await db.posts.find({'thread': int(thread['count'])}).sort(
                    [('date', -1)]
                ).limit(limit).to_list(None)
                for p in posts:
                    if p.get('files'):
                        for f in p['files']:
                            if f['filetype']:
                                thread['filecount'] -= 1
                thread['latest'] = posts
            admin = self.user.is_admin
            popup = None
            if self.get_arguments('err'):
                errors = {
                    'empty': 'Empty posts not allowed',
                    'notfound': 'Thread not found',
                    'bl': 'Your post contained words from blacklist',
                }
                error = self.get_argument('err')
                popup = errors.get(error)
            if self.get_arguments('page'):
                try:
                    page = int(self.get_argument('page'))
                except ValueError:
                    page = 0
            else:
                page = 0
            threads_list = await self.chunkify(threads, db_board)
            try:
                threads = threads_list[page]
            except IndexError:
                try:
                    threads = threads_list[0]
                except IndexError:
                    pass
            current = 0
            if len(threads_list) > 1:
                paged = []
                url = self.request.uri.split('?')[0]
                for x in range(len(threads_list)):
                    paged.append({
                        'numb': x,
                        'url': url + '?page=' + str(x),
                    })
                    if x == page:
                        current = x
            else:
                paged = None
            pinned_thread = None
            if db_board['pinned']:
                pinned_thread = await db.posts.find_one({'count': int(db_board['pinned'])})
            await self.render(
                'board.html',
                threads=threads, board=db_board, boards=await self.boards, admin=admin, show=True,
                banner=banner, popup=popup, paged=paged, current=current, pind=pinned_thread
            )
        else:
            self.redirect('/')

    async def post(self, board):
        db = self.database
        ip = await get_ip(self.request)
        if not await is_banned(db, ip, board):
            # db_board = await db.boards.find_one({'short': board})
            # threads = await db['posts'].find({'board': board,'oppost': True}).sort(
            #     [('lastpost', -1)]
            # ).limit(db_board['thread_catalog']).to_list(None)
            subject = self.get_argument('subject', '')
            password = self.get_argument('pass', '')
            text = self.get_argument('text', '')
            username = self.get_argument('username', '') or False
            text = strip_tags(text)
            text = text.replace('&gt;', '>')
            text = text.strip()
            if has_blacklisted_words(text):
                self.redirect(f'/{board}?err=bl')
            else:
                # noinspection SpellCheckingInspection
                spoiler = 'spoilerimage' in self.request.arguments
                # noinspection SpellCheckingInspection
                showop = 'showop' in self.request.arguments
                files = []
                if self.request.files:
                    for x in ['file1', 'file2', 'file3', 'file4']:
                        if self.request.files.get(x):
                            if file_details := await upload_file(self.request.files[x][0]):
                                fo, ff, filetype, filedata = file_details
                                files.append({'original': fo, 'name': ff, 'filetype': filetype, 'filedata': filedata})
                global latest_postnumber
                latest_postnumber += 1
                count = latest_postnumber
                oppost = True
                thread = None
                admin = False
                # noinspection SpellCheckingInspection
                sage = 'saging' in self.request.arguments
                admin = self.current_user.is_admin and 'admin' in self.request.arguments
                if subject or text or files:
                    data = await makedata(
                        db, subject, text, count, board, ip, oppost, thread, files, username,
                        spoiler=spoiler, admin=admin, sage=sage, opip=ip, showop=showop, password=password
                    )
                    await db.posts.insert_one(data)
                    await log('post', f'IP {ip} created a thread {count} in {board} board.')
                    self.redirect('/' + board + '/thread/' + str(data['count']))
                else:
                    self.redirect(self.request.uri + '?err=empty')
        else:
            self.redirect('/banned')

    @staticmethod
    async def chunkify(list_of_threads: list[dict], n: dict[str, int]):
        res = list()
        n = int(n.get('perpage', 10))
        for i in range(0, len(list_of_threads), n):
            res.append(list_of_threads[i:i + n])
        return res


# catalog of threads
class CatalogHandler(UserHandler):

    async def get(self, board):
        db = self.database
        db_board = await db.boards.find_one({'short': board})
        if db_board:
            threads = await db.posts.find(
                {'board': board,'oppost': True}
            ).sort(
                [('pinned', -1), ('lastpost', -1)]
            ).limit(db_board['thread_catalog']).to_list(None)
            for thread in threads:
                if thread.get('files'):
                    thread['file'] = thread['files'][0]
            await self.render('catalog.html', threads=threads, board=db_board, boards=await self.boards)
        else:
            self.redirect('/')


# posts in thread
class ThreadHandler(UserHandler):
    thread_count = ''

    async def get(self, board, count):
        thread_count = int(count)
        db = self.database
        db_board = await db.boards.find_one({'short': board})
        if db_board:
            banner = None
            if db_board['banners']:
                banner = random.choice(db_board['banners'])
            posts = await db['posts'].find({'thread': thread_count}).sort([('count', 1)]).to_list(None)
            op = await db['posts'].find_one({"count": thread_count, 'oppost': True})
            if op:
                if not op['infinite']:
                    if await check_thread(db, thread_count, db_board['thread_posts']):
                        op['locked'] = True
                        await update_db(db, op['count'], op)
                admin = self.current_user.is_admin
                op = await db.posts.find_one({'count': int(count)})
                ip = await get_ip(self.request)
                popup = None
                if self.get_arguments('err'):
                    error = self.get_argument('err')
                    if error == 'empty':
                        popup = "Empty posts not allowed."
                    else:
                        popup = None
                await self.render(
                    'posts.html', op=op, posts=posts, board=db_board, boards=await self.boards,
                    admin=admin, show=op['ip'] == ip, banner=banner, popup=popup
                )

            else:
                self.redirect(f'/{board}?err=notfound')
        else:
            self.redirect('/')

    async def post(self, board, thread_count):
        db = self.database
        ip = await get_ip(self.request)
        if not await is_banned(db, ip, board):
            thread_count = int(thread_count)
            subject = self.get_argument('subject', '')
            password = self.get_argument('pass', '')
            text = self.get_argument('text', 'empty post')
            text = strip_tags(text)
            text = text.replace('&gt;', '>')
            if has_blacklisted_words(text):
                self.redirect(f'/{board}?err=bl')
            else:
                username = self.get_argument('username', '') or False
                files = []
                if self.request.files:
                    for x in ['file1', 'file2', 'file3', 'file4']:
                        if self.request.files.get(x):
                            fo, ff, filetype, filedata = await upload_file(self.request.files[x][0])
                            if fo and ff and filetype and filedata:
                                files.append({
                                    'original': fo,
                                    'name': ff,
                                    'filetype': filetype,
                                    'filedata': filedata
                                })
                replies = get_replies(text)
                text = text.strip()
                # TODO: fix this garbage
                global latest_postnumber
                latest_postnumber += 1
                count = latest_postnumber
                oppost = False
                thread = thread_count  # wtf why
                op = await db.posts.find_one({'count': int(thread)})
                ip = await get_ip(self.request)
                spoiler = 'spoilerimage' in self.request.arguments
                sage = 'saging' in self.request.arguments
                showop = 'showop' in self.request.arguments
                admin = self.current_user.is_admin and 'admin' in self.request.arguments
                if subject or text or files:
                    data = await makedata(
                        db, subject, text, count, board, ip, oppost, thread, files,
                        username, spoiler=spoiler, admin=admin, sage=sage, opip=op['ip'],
                        showop=showop, password=password
                    )
                    await db.posts.insert_one(data)
                    # FIXME: what if that's an oppost ?
                    log_message = f'{ip} posted #{count} in a thread #{thread} on {board} board.'
                    await log('post', log_message)
                    op = await db['posts'].find_one({'count': thread_count})
                    if op:
                        db_board = await db.boards.find_one({'short': board})
                        if not op['locked']:
                            if not await check_thread(db, thread_count, db_board['thread_bump']):
                                if not data['sage']:
                                    if not data['subject'].lower() == 'sage':
                                        op['lastpost'] = datetime.datetime.utcnow()
                                        await update_db(db, op['count'], op)
                            for number in replies:
                                p = await db.posts.find_one({'count': int(number)})
                                old_replies = p['replies']
                                if int(data['count']) not in old_replies:
                                    old_replies.append(int(data['count']))
                                    p['replies'] = old_replies
                                    await update_db(db, p['count'], p)
                        if op:
                            if await check_thread(db, thread_count, db_board['thread_posts']):
                                if not op['infinite']:
                                    op['locked'] = True
                                    await update_db(db, op['count'], op)
                                else:
                                    posts = await db.posts.find(
                                        {'thread': thread_count}
                                    ).sort([('count', 1)]).to_list(None)
                                    p = posts[0]
                                    await remove_files(p)
                                    await db.posts.delete_one({'count': p['count']})

                        self.redirect('/' + str(board) + '/thread/' + str(op['count']))
                    else:
                        self.redirect('/' + str(board))
                else:
                    self.redirect(self.request.uri + '?err=empty')
        else:
            self.redirect('/banned')


class JsonBoardHandler(UserHandler):
    thread_count = ''

    async def check_origin(self, origin):
        return True

    async def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')

    async def options(self):
        self.set_status(204)
        await self.finish()

    async def get(self, board):
        db = self.database
        exclude_fields = ['_id', 'ip', 'pass']
        threads = []
        # this is unreadable
        raw_threads = db.posts.find(
            {'board': board, 'oppost': True}, exclude(exclude_fields)
        ).sort([('pinned', -1), ('lastpost', -1)])
        async for thread in raw_threads:
            thread['date'] = thread['date'].strftime("%Y-%m-%d %H:%M:%S")
            thread['lastpost'] = thread['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
            threads.append(thread)
        self.write(json.dumps(threads, indent=4, ensure_ascii=False))


class JsonThreadHandler(UserHandler):
    thread_count = ''

    async def check_origin(self, origin):
        return True

    async def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')

    async def options(self):
        self.set_status(204)
        await self.finish()

    async def get(self, board, count):
        thread_count = int(count)
        db = self.database
        op_exclude_fields = ['_id', 'ip', 'pass']
        op = await db.posts.find_one({'count': thread_count}, exclude(op_exclude_fields))
        op['date'] = op['date'].strftime("%Y-%m-%d %H:%M:%S")
        op['lastpost'] = op['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
        op = dict(filter(lambda item: item[1] is not None, op.items()))
        res = [op]
        exclude_fields = ['_id', 'ip', 'pass']
        posts = await db['posts'].find(
            {'thread': thread_count}, exclude(exclude_fields)
        ).sort([('count', 1)]).to_list(None)
        for post in posts:
            post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
            post = dict(filter(lambda p: p[1] is not None, post.items()))
            res.append(post)
        self.write(json.dumps(res, indent=4, ensure_ascii=False))


async def upload_file(file_to_upload: dict[str, str]) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    filename = file_to_upload.get('filename')
    extension = os.path.splitext(filename)[-1].lower()
    if extension in ['.jpg', '.gif', '.png','.jpeg']:
        filetype = 'image'
    elif extension in ['.webm', '.mp4']:
        filetype = 'video'
    elif extension in ['.mp3', '.ogg', '.wav', '.opus']:
        filetype = 'audio'
    else:
        # if format not supported
        return None, None, None, None
    new_name = os.path.join(uploads, f"{uuid4().hex}{extension}")
    with open(new_name, 'wb') as nf:
        nf.write(bytes(file_to_upload.get('body')))
    filedata = await process_file(new_name)
    return filename, new_name, filetype, filedata


async def convert_bytes(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


async def process_file(filepath: os.PathLike[str]) -> Optional[str]:
    if os.path.isfile(filepath):
        filesize = await convert_bytes(os.stat(filepath).st_size)
        extension = os.path.splitext(filepath)[-1].upper()
        file_type = get_filetype(filepath)
        if file_type is FileTypes.VIDEO:
            w, h = resolution(filepath)
        elif file_type is FileTypes.IMAGE:
            with Image.open(filepath) as img:
                w, h = img.size
        elif file_type is FileTypes.AUDIO:
            return f'{extension}, {filesize}'
        else:
            return None
        return f'{extension}, {w}x{h}, {filesize}'
    return None


# ban status for your ip
class BannedHandler(UserHandler):
    # TODO: associate uid with IPs and bans
    async def get(self):
        ip = await get_ip(self.request)
        ban = await self.database.bans.find_one({'ip': ip}) or None
        await self.render('banned.html', ban=ban, boards=None)


class AboutHandler(UserHandler):
    async def get(self):
        await self.render('about.html', boards=None)


# TODO: do a proper fucking job - use a class perhaps?
# constructs dictionary to insert into mongodb
async def makedata(
    db, subject, text, count, board, ip, oppost=False,
    thread=None, files=[], username=False, spoiler=False,
    admin=False, sage=False, opip='',
    showop=False, password='abcde'
):
    data = {}
    data['ip'] = ip
    data['subject'] = subject
    data['text'] = text
    data['count'] = count
    data['board'] = board
    data['date'] = datetime.datetime.utcnow()
    data['oppost'] = oppost
    data['thread'] = thread
    data['banned'] = False
    data['ban_message'] = None
    data['replies'] = []
    data['country'] = ''
    data['countryname'] = ''
    data['trip'] = None
    data['admin'] = admin
    data['sage'] = sage
    data['roll'] = None
    data['files'] = files
    data['seal'] = False
    data['op'] = ip == opip and showop
    if password == '':
        password = uuid4().hex[:5]
    data['pass'] = password
    if data['subject'].lower() == 'sage':
        data['sage'] = True
    b = await db.boards.find_one({'short': board})
    if b['country']:
        # workaround for localhost, replaces localhost with google ip (US)
        if ip == '127.0.0.1':
            ip = '172.217.20.206'
        gdbr_data = gdbr.city(ip)
        data['country'] = gdbr_data.country.iso_code
        # TODO: load from external file
        extraflags = ['Bavaria', 'Scotland', 'Wales']
        # TODO: load from external file
        # exceptions for IPs that are incorrectly detected, has to be changed manually smh
        ip_exceptions = {
            "80.128.":'Bavaria',
            "95.91.205": 'Bavaria'
        }
        is_in_exceptions = [v for k,v in ip_exceptions.items() if ip.startswith(k)]
        # TODO: make this into separate function
        if gdbr_data.subdivisions.most_specific.name in extraflags:
            data['country'] = gdbr_data.subdivisions.most_specific.name
            data['countryname'] = data['country']
        elif is_in_exceptions:
            data['country'] = data['countryname'] = is_in_exceptions[0]
        else:
            try:
                data['countryname'] = regioncodes.get(data['country'])
            except KeyError:
                data['countryname'] = 'Proxy'
                data['country'] = 'PROXY'
        mapdata = {
            'countryname': data['countryname'],
            'country': data['country'],
            'long': gdbr_data.location.longitude,
            'lat': gdbr_data.location.latitude,
            'date': datetime.datetime.utcnow()
        }
        await check_map(db, mapdata)
        await db.maps.insert_one(mapdata)
    if b['roll']:
        data['roll'] = await roll(data['subject'])
    if not b['custom']:
        if b['username'] != '':
            data['username'] = b['username']
        else:
            data['username'] = None
    else:
        if username and username != '':
            if '#' in username:
                uname, trip = username.split('#')
                data['username'] = uname
                data['trip'] = '!' + tripcode(trip)
            else:
                data['username'] = username
        else:
            if b['username'] != '':
                data['username'] = b['username']
            else:
                data['username'] = None

    t = None
    if oppost:
        data['locked'] = False
        data['lastpost'] = datetime.datetime.utcnow()
        data['postcount'] = 0
        data['filecount'] = 0
        data['pinned'] = False
        data['infinite'] = False
    elif thread:
        t = await db.posts.find_one({'count': thread})
        postcount = int(await db.posts.count_documents({'thread': t['count']}))
        t['postcount'] = postcount + 1
        await update_db(db, t['count'], t)
    if files:
        b['mediacount'] = b['mediacount'] + 1
        for f in files:
            if f['filetype'] in ['image', 'video']:
                if not spoiler:
                    f['thumb'] = await make_thumbnail(f['name'])
                else:
                    f['thumb'] = spoilered
            else:
                f['thumb'] = None
        if not oppost and t:
            # TODO: check if the fix works
            filecount = sum([
                len(file.get('files', [])) for file in await db.posts.find(
                    {'thread': t['count'], 'files': {'$ne': None}}
                ).to_list(None)
            ])
            t['filecount'] = filecount + 1
            await update_db(db, t['count'], t)
    else:
        data['image'] = data['video'] = None
    b['postcount'] = int(b['postcount']) + 1
    await update_db_b(db, b['short'], b)
    return data


# this is an ugly hack that works somehow
# need to rework so that deleted post numbers cant be reused
async def latest(db):
    try:
        return list(await db['posts'].find({}).sort('count', -1).to_list(None))[0]['count']
    except Exception as e:
        return 0


# checks if number of posts in thread exceeds whatever number you check it against
async def check_thread(db, thread, subj):
    return await db.posts.count_documents({'thread': thread}) >= subj - 1


# TODO: move into a celery task lmao wtf is this shitcode
# deletes the threads that are inactive after there are too much threads
def schedule_check(app):
    next_time = datetime.timedelta(0, default_settings.CHECK_TIMEOUT)

    @tornado.gen.coroutine
    def task():
        # delete all threads except first N, sorted by bumps
        db = app.database
        boards = yield db.boards.find({}).to_list(None)
        try:
            for board in boards:
                threads = yield db.posts.find(
                    {
                        'oppost': True,
                        'board': board['short']
                    }
                ).sort('lastpost', 1).to_list(None)
                if not len(threads) <= board['thread_catalog']:
                    threads = threads[:(len(threads) - board['thread_catalog'])]
                    for thread in threads:
                        if not thread['pinned']:
                            synchronize_removal(thread)
                            posts = yield db.posts.find({'thread': thread['count']}).to_list(None)
                            for post in posts:
                                synchronize_removal(post)
                            yield db.posts.delete_many({'thread': thread['count']})
                            yield db.posts.remove({'count': thread['count']})
        except Exception as e:
            logger.critical('Error processing scheduled check', exc_info=e)
            print(repr(e))
            pass

    def wrapper():
        executor.submit(task)
        schedule_check(app)

    tornado.ioloop.IOLoop.current().add_timeout(next_time, wrapper)


# TODO: store ban information in User
async def is_banned(db, ip, board):
    # wtf even is this
    ban = await db.bans.find_one({'ip': ip})
    if board not in default_settings.BAN_ALLOWED:
        if ban:
            if ban['date']:
                expires = datetime.datetime.strptime(ban['date'], "%a, %d %b %Y %H:%M:%S %Z")
                if expires > datetime.datetime.utcnow():
                    return True
                else:
                    await db.bans.delete_one({'ip': ip})
                    log_message = f'{ip} was unbanned (banned until {ban["date"]}).'
                    logging.info(log_message)
                    await log('unban', log_message)
                    return False
            else:
                return True
        return False
    else:
        if ban:
            if ban['date']:
                return False
            return True
        return False


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/$', IndexHandler),
            (r'/map/?', MapHandler),
            (r'/admin/?', AdminHandler),
            (r'/banned/?', BannedHandler),
            (r'/about/?', AboutHandler),
            (r'/profile/?', ProfilePage),
            (r'/flags/(.*)/?', tornado.web.StaticFileHandler, {'path': os.path.join('src', 'flags')}),
            (r'/banners/(.*)/?', tornado.web.StaticFileHandler, {'path': os.path.join('src', 'banners')}),
            (r'/(\w+)/?', BoardHandler),
            (r'/(\w+)/json/?', JsonBoardHandler),
            (r'/(\w+)/catalog/?', CatalogHandler),
            (r'/(\w+)/thread/(\d+)/?', ThreadHandler),
            (r'/(\w+)/thread/(\d+)/new/?', AjaxNewHandler),
            (r'/(\w+)/thread/(\d+)/json/?', JsonThreadHandler),

            # ADMIN
            (r'/admin/login/?', AdminLoginHandler),
            (r'/admin/logout/?', AdminLogoutHandler),
            (r'/admin/create/?', AdminBoardCreationHandler),
            (r'/admin/edit/(\w+)/?', AdminBoardEditHandler),
            (r'/admin/stats/?', AdminStatsHandler),
            (r'/admin/bans/?', AdminBannedHandler),
            (r'/admin/reports/?', AdminReportsHandler),
            (r'/admin/logs/?', AdminLogsHandler),
            (r'/admin/blacklist/?', AdminBlackListHandler),
            (r'/admin/search/(\d+)/?', AdminIPSearchHandler),
            # (r'/uploads/(.*)/?', tornado.web.StaticFileHandler, {'path': os.path.join('src', uploads)}),
            (r'/uploads/(.*)/?', tornado.web.StaticFileHandler, {'path': uploads}),

            # AJAX - needs to be rewritten
            (r'/ajax/remove/?', AjaxDeleteHandler),
            (r'/ajax/delete/?', AjaxDeletePassHandler),
            (r'/ajax/ban/?', AjaxBanHandler),
            (r'/ajax/report/?', AjaxReportHandler),
            (r'/ajax/info/?', AjaxInfoHandler),
            (r'/ajax/pin/?', AjaxPinHandler),
            (r'/ajax/pin_thread/?', AjaxThreadPinHandler),
            (r'/ajax/lock/?', AjaxLockHandler),
            (r'/ajax/get/?', AjaxPostGetter),
            (r'/ajax/banner-del/?', AjaxBannerDelHandler),
            (r'/ajax/move/?', AjaxMoveHandler),
            (r'/ajax/infinify/?', AjaxInfinifyHandler),
            (r'/ajax/map/?', AjaxMapHandler),
            (r'/ajax/seal/?', AjaxSealHandler),

            # API
            (r'/api/boards/?', GetBoards),
            (r'/api/boards/(\w+)/?', GetThreads),
            (r'/api/boards/(\w+)/(\d+)/?', GetPosts),
        ]

        settings = {
            'ui_modules': uimodules,
            'template_path': 'templates',
            'static_path': 'static',
            'xsrf_cookies': True,
            'cookie_secret': "__#TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        }

        self.con = motor.motor_tornado.MotorClient('localhost', 27017)
        self.database = self.con['imageboard']
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    logger.info('Starting up the server...')
    check_path(uploads)
    check_path('banners/')
    tornado.options.parse_command_line()
    # TODO: import env variables and run as DEBUG-only
    tornado.autoreload.start()

    application = Application()
    # holy fuck this is awful
    global latest_postnumber

    try:
        latest_con = pymongo.MongoClient('localhost', 27017)
    except pymongo.errors.ServerSelectionTimeoutError:
        logger.error('MongoDB is not running.')

    latest_db = latest_con['imageboard']

    try:
        latest_postnumber = latest_db['posts'].find({}).sort('count', -1)[0]['count']
    except IndexError:
        # in case you are running the server for the first time
        # there will be no posts therefore this should return 0
        # and the first post will be №1
        latest_postnumber = 0

    http_server = tornado.httpserver.HTTPServer(application, max_buffer_size=default_settings.MAX_FILESIZE)
    http_server.listen(options.port)
    logger.info(f'Server is running on {options.port}')
    schedule_check(application)
    tornado.ioloop.IOLoop.instance().start()

