# -*- coding: utf-8 -*-
import tornado.options
import tornado.httpserver
import tornado.web
import tornado.ioloop
import motor.motor_tornado
import uimodules
import datetime
import ib_settings as _ib
from tornado import concurrent
import re
from uuid import uuid4
import os
from mimetypes import guess_type
import json
from getresolution import resolution
from tornado import gen
from html.parser import HTMLParser
from PIL import Image
import geoip2.database as gdb
from thumbnail import make_thumbnail
from tripcode import tripcode
import random

from logger import log

from admin import *
from ajax import *
from utils import *

from tornado.options import define, options
define('port', default=8000, help='run on given port', type=int)

executor = concurrent.futures.ThreadPoolExecutor(8)

uploads = 'uploads/'

with open('static/regioncodes.json') as f:
    regioncodes = json.loads(f.read())

def check_path(path):
    if not os.path.exists(path):
        os.makedirs(path)

gdbr = gdb.Reader('GeoLite2-City.mmdb')

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


# this is done to ensure user does not input any html in posting form
def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


async def roll(subject):
    matches = re.compile(r'r(oll)? ([1-9])d([1-9]$|[1-9][0-9]{0,3}$)').match(subject)
    if not matches:
        return None
    count = int(matches.group(2))
    sides = int(matches.group(3))
    return 'Rolled {}'.format(','.join(str(random.randint(0, sides)) for i in range(count)))


# list of boards
class IndexHandler(tornado.web.RequestHandler):

    async def get(self):
        db = self.application.database
        boards = await db.boards.find({}).to_list(None) or None
        boards_list = await db.boards.find({}).to_list(None) or None
        self.render('index.html', boards=boards, boards_list=boards_list)


# map of posters
class MapHandler(tornado.web.RequestHandler):

    async def get(self):
        db = self.application.database
        boards = await db.boards.find({}).to_list(None) or None
        boards_list = await db.boards.find({}).to_list(None) or None
        self.render('map.html', boards=boards, boards_list=boards_list)


# list of threads
class BoardHandler(LoggedInHandler):

    async def get(self, board):
        db = self.application.database
        db_board = await db.boards.find_one({'short': board})
        if db_board:
            if db_board['banners']:
                banner = random.choice(db_board['banners'])
            else: banner = None
            threads = await db.posts.find({'board': board,'oppost': True}).sort([('pinned', -1), ('lastpost', -1)]).limit(db_board['thread_catalog']).to_list(None)
            boards_list = await db.boards.find({}).to_list(None)
            for thread in threads:
                limit = 3
                if thread['pinned']: limit = 1
                posts = await db.posts.find({'thread': int(thread['count'])}).sort([('date', -1)]).limit(limit).to_list(None)
                posts.reverse()
                for p in posts:
                    if p['filetype']:
                        thread['filecount'] -= 1
                thread['latest'] = posts
            admin = False
            if self.current_user: admin = True
            popup = None
            if self.get_arguments('err') != []:
                errors = {'empty': 'Empty posts not allowed',
                            'notfound': 'Thread not found', }
                error = self.get_argument('err')
                popup = errors.get(error)
            if self.get_arguments('page') != []:
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
            self.render('board.html', threads=threads, board=db_board, boards_list=boards_list, admin=admin, show=True,
                banner=banner, popup=popup, paged=paged, current=current)
        else:
            self.redirect('/')

    async def post(self, board):
        db = self.application.database
        ip = await get_ip(self.request)
        if not await is_banned(db, ip, board):
            db_board = await db.boards.find_one({'short': board})
            threads = await db['posts'].find({'board': board,'oppost': True}).sort([('lastpost', -1)]).limit(db_board['thread_catalog']).to_list(None)
            subject = self.get_argument('subject', '')
            password = self.get_argument('pass', '')
            text = self.get_argument('text', '')
            username = self.get_argument('username', '') or False
            text = strip_tags(text)
            spoiler = 'spoilerimage' in self.request.arguments
            showop = 'showop' in self.request.arguments
            if self.request.files:
                fo, ff, filetype, filedata = await upload_file(self.request.files['file'][0])
            else:
                fo = ff = filetype = filedata = None
            count = await latest(db) + 1
            oppost = True
            thread = None
            admin = False
            sage = 'saging' in self.request.arguments
            if self.current_user and 'admin' in self.request.arguments: admin = True
            if subject or text or fo:
                data = await makedata(db, subject, text, count, board, ip, oppost, thread, fo, ff, filetype, filedata,
                username, spoiler=spoiler, admin=admin, sage=sage, opip=ip, showop=showop, password=password)
                await db.posts.insert(data)
                log_message = '{0} created a thread {1} in {2}.'.format(ip, count, board)
                await log('post', log_message)
                self.redirect('/' + board + '/thread/' + str(data['count']))
            else:
                self.redirect(self.request.uri + '?err=empty')
        else:
            self.redirect('/banned')

    async def chunkify(self, l, n):
        res = list()
        n = int(n['perpage'])
        for i in range(0, len(l), n):
            res.append(l[i:i + n])
        return res

# catalog of threads
class CatalogHandler(tornado.web.RequestHandler):

    async def get(self, board):
        db = self.application.database
        db_board = await db.boards.find_one({'short': board})
        if db_board:
            threads = await db.posts.find({'board': board,'oppost': True}).sort([('pinned', -1), ('lastpost', -1)]).limit(db_board['thread_catalog']).to_list(None)
            boards_list = await db.boards.find({}).to_list(None)
            self.render('catalog.html', threads=threads, board=db_board, boards_list=boards_list)
        else:
            self.redirect('/')


# posts in thread
class ThreadHandler(LoggedInHandler):
    thread_count = ''

    async def get(self, board, count):
        thread_count = int(count)
        db = self.application.database
        db_board = await db.boards.find_one({'short': board})
        if db_board:
            if db_board['banners']:
                banner = random.choice(db_board['banners'])
            else: banner = None
            posts = await db['posts'].find({'thread': thread_count}).sort([('count', 1)]).to_list(None)
            op = await db['posts'].find_one({"count": thread_count, 'oppost': True})
            if op:
                if not op['infinite']:
                    if await check_thread(db, thread_count, db_board['thread_posts']):
                        op['locked'] = True
                        await update_db(db, op['count'], op)
                boards_list = await db.boards.find({}).to_list(None)
                admin = False
                if self.current_user: admin = True
                op = await db.posts.find_one({'count': int(count)})
                ip = await get_ip(self.request)
                popup = None
                if self.get_arguments('err') != []:
                    error = self.get_argument('err')
                    if error == 'empty':
                        popup = "Empty posts not allowed."
                    else:
                        popup = None
                self.render('posts.html', op=op, posts=posts, board=db_board, boards_list=boards_list, admin=admin,
                            show=op['ip']==ip, banner=banner, popup=popup)

            else:
                self.redirect('/' + board + '?err=notfound')
        else:
            self.redirect('/')

    async def post(self, board, thread_count):
        db = self.application.database
        ip = await get_ip(self.request)
        if not await is_banned(db, ip, board):
            thread_count = int(thread_count)
            subject = self.get_argument('subject', '')
            password = self.get_argument('pass', '')
            text = self.get_argument('text', 'empty post')
            text = strip_tags(text)
            text = text.replace("\n","<br />")
            username = self.get_argument('username', '') or False
            if self.request.files:
                foriginal, ffile, filetype, filedata = await upload_file(self.request.files['file'][0])
            else:
                foriginal = ffile = filetype = filedata = None
            replies = get_replies(text)
            count = await latest(db) + 1
            oppost = False
            thread = thread_count #wtf why
            op = await db.posts.find_one({'count': int(thread)})
            ip = await get_ip(self.request)
            spoiler = 'spoilerimage' in self.request.arguments
            sage = 'saging' in self.request.arguments
            showop = 'showop' in self.request.arguments
            admin = False
            if self.current_user and 'admin' in self.request.arguments: admin = True
            if subject or text or foriginal:
                data = await makedata(db, subject, text, count, board, ip, oppost, thread, foriginal, ffile, filetype, filedata,
                    username, spoiler=spoiler, admin=admin, sage=sage, opip=op['ip'], showop=showop, password=password)
                await db.posts.insert(data)
                log_message = '{0} posted #{1} in a thread #{2} on {3} board.'.format(ip, count, thread, board)
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
                    if op != None:
                        if await check_thread(db, thread_count, db_board['thread_posts']):
                            if not op['infinite']:
                                op['locked'] = True
                                await update_db(db, op['count'], op)
                            else:
                                posts = await db['posts'].find({'thread': thread_count}).sort([('count', 1)]).to_list(None)
                                p = posts[0]
                                await removeing(p)
                                await db.posts.delete_one({'count': p['count']})

                    self.redirect('/' + str(board) + '/thread/' + str(op['count']))
                else:
                    self.redirect('/' + str(board))
            else:
                self.redirect(self.request.uri + '?err=empty')
        else:
            self.redirect('/banned')


class JsonThreadHandler(LoggedInHandler):
    thread_count = ''

    async def get(self, board, count):
        thread_count = int(count)
        db = self.application.database
        db_board = await db.boards.find_one({'short': board})
        op = await db.posts.find_one({'count': thread_count})
        del op['_id']
        del op['ip']
        del op['pass']
        op['date'] = op['date'].strftime("%Y-%m-%d %H:%M:%S")
        op['lastpost'] = op['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
        op = {k:v for k,v in op.items() if v != None}
        res = [op]
        posts = await db['posts'].find({'thread': thread_count}).sort([('count', 1)]).to_list(None)
        for post in posts:
            del post['_id']
            del post['ip']
            del post['pass']
            post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
            post = {k:v for k,v in post.items() if v != None}
            res.append(post)
        self.write(json.dumps(res, indent=4, ensure_ascii=False))


async def upload_file(f):
    fname = f['filename']
    fext = os.path.splitext(fname)[1].lower()
    if fext in ['.jpg', '.gif', '.png','.jpeg']:
        filetype = 'image'
    elif fext in ['.webm', '.mp4']:
        filetype = 'video'
    elif fext in ['.mp3', '.ogg', '.wav', '.opus']:
        filetype = 'audio'
    else:
        # if format not supported
        return None, None, None, None
    newname = uploads + str(uuid4()) + fext
    with open(newname, 'wb') as nf:
        nf.write(bytes(f['body']))
    filedata = await process_file(newname)
    return fname, newname, filetype, filedata


async def convert_bytes(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


async def process_file(fn):

    if os.path.isfile(fn):
        filesize = await convert_bytes((os.stat(fn).st_size))
        if fn.endswith(('webm', 'mp4')):
            w,h = resolution(fn)
        elif fn.endswith(('png', 'jpg', 'jpeg', 'gif')):
            with Image.open(fn) as img:
                w, h = img.size
        elif fn.endswith(('ogg', 'mp3', 'wav', 'opus')):
            return '{0}, {1}'.format(fn.split('.')[-1].upper(), filesize)
        else:
            return False
        return '{0}, {1}x{2}, {3}'.format(fn.split('.')[-1].upper(), w, h, filesize)
    else:
        return False


# ban status for your ip
class BannedHandler(tornado.web.RequestHandler):
    async def get(self):
        db = self.application.database
        ip = await get_ip(self.request)
        ban = await db.bans.find_one({'ip':ip}) or None
        self.render('banned.html', ban=ban, boards_list=None)


# constructs dictionary to insert into mongodb
async def makedata(db, subject, text, count, board, ip, oppost=False, thread=None, fo=None, f=None, filetype=None,
                    filedata=False, username=False, spoiler=False, admin=False, sage=False, opip='', showop=False,
                    password='abcde'):
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
    data['replies'] = []
    data['country'] = ''
    data['countryname'] = ''
    data['trip'] = None
    data['image'] = None
    data['video'] = None
    data['audio'] = None
    data['admin'] = admin
    data['thumb'] = None
    data['sage'] = sage
    data['roll'] = None
    data['filetype'] = None
    data['op'] = ip == opip and showop
    if password == '':
        password = 'abcde'
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
        extraflags = ['Bavaria', 'Scotland', 'Wales']
        if gdbr_data.subdivisions.most_specific.name in extraflags:
            data['country'] = gdbr_data.subdivisions.most_specific.name
            data['countryname'] = data['country']
        else:
            data['countryname'] = regioncodes[data['country']]
        mapdata = {'countryname': data['countryname'],
                    'country': data['country'],
                    'long': gdbr_data.location.longitude,
                    'lat': gdbr_data.location.latitude,
                    'date': datetime.datetime.utcnow()}
        await check_map(db, mapdata)
        await db.maps.insert(mapdata)
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
    if thread:
        t = await db.posts.find_one({'count': thread})
    if oppost:
        data['locked'] = False
        data['lastpost'] = datetime.datetime.utcnow()
        data['postcount'] = 0
        data['filecount'] = 0
        data['pinned'] = False
        data['infinite'] = False
    else:
        postcount = int(await db.posts.find({'thread': t['count']}).count())
        t['postcount'] = postcount + 1
        await update_db(db, t['count'], t)
    if f:
        b['mediacount'] = b['mediacount'] + 1
        data['original'] = fo
        data[filetype] = f
        data['filetype'] = filetype
        if not spoiler:
            data['thumb'] = await make_thumbnail(f)
        else:
            data['thumb'] = spoilered
        if not oppost:
            filecount = await db.posts.find({'thread': t['count'],
                                        'image': { '$ne': None }
                                        }).count() + await db.posts.find({'thread': t['count'],
                                                                    'video': {'$ne': None}}).count()
            t['filecount'] = filecount + 1
            await update_db(db, t['count'], t)
        if filedata:
            data['filedata'] = filedata
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
    return await db.posts.find({'thread': thread}).count() >= subj - 1


# deletes the threads that are inactive after there are too much threads
def schedule_check(app):
    next_time = datetime.timedelta(0, _ib.CHECK_TIMEOUT)
    @tornado.gen.coroutine
    def task():
        # delete all threads except first N, sorted by bumps
        db = app.database
        boards = yield db.boards.find({}).to_list(None)
        try:
            for board in boards:
                threads = yield db.posts.find({'oppost': True,
                                        'board': board['short']}).sort('lastpost', 1).to_list(None)
                if not len(threads) <= board['thread_catalog']:
                    threads = threads[:(threads.count(None) - board['thread_catalog'])]
                    for thread in threads:
                        if not thread['pinned']:
                            sync_removeing(thread)
                            posts = yield db.posts.find({'thread': thread['count']}).to_list(None)
                            for post in posts:
                                sync_removeing(post)
                            yield db.posts.delete_many({'thread': thread['count']})
                            yield db.posts.remove({'count': thread['count']})
        except Exception as e:
            print(repr(e))
            pass
    def wrapper():
        executor.submit(task)
        schedule_check(app)
    tornado.ioloop.IOLoop.current().add_timeout(next_time, wrapper)


async def is_banned(db, ip, board):
    if board not in _ib.BAN_ALLOWED:
        ban = await db.bans.find_one({'ip': ip})
        if ban:
            if ban['date']:
                expires = datetime.datetime.strptime(ban['date'], "%d-%m-%Y")
                if expires > datetime.datetime.today():
                    return True
                else:
                    await db.bans.delete_one({'ip': ip})
                    log_message = '{0} was unbanned (banned until {1}).'.format(ip, ban['date'])
                    await log('unban', log_message)
                    return False
            else:
                return True
        return False
    else:
        return False


def get_replies(text):
    replies = []
    x = re.compile(r'(>>\d+)')
    it = re.finditer(x, text)
    for x in it:
        number = x.group(0)
        replies.append(int(number[2:]))
    return replies


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/$', IndexHandler),
            (r'/map/?', MapHandler),
            (r'/admin/?', AdminHandler),
            (r'/banned/?', BannedHandler),
            (r'/flags/(.*)/?', tornado.web.StaticFileHandler, {'path': 'flags'}),
            (r'/banners/(.*)/?', tornado.web.StaticFileHandler, {'path': 'banners'}),
            (r'/(\w+)/?', BoardHandler),
            (r'/(\w+)/catalog/?', CatalogHandler),
            (r'/(\w+)/thread/(\d+)/?', ThreadHandler),
            (r'/(\w+)/thread/(\d+)/new/?', AjaxNewHandler),
            (r'/(\w+)/thread/(\d+)/json/?', JsonThreadHandler),
            (r'/admin/login/?', AdminLoginHandler),
            (r'/admin/logout/?', AdminLogoutHandler),
            (r'/admin/create/?', AdminBoardCreationHandler),
            (r'/admin/edit/(\w+)/?', AdminBoardEditHandler),
            (r'/admin/stats/?', AdminStatsHandler),
            (r'/admin/bans/?', AdminBannedHandler),
            (r'/admin/reports/?', AdminReportsHandler),
            (r'/admin/logs/?', AdminLogsHandler),
            (r'/uploads/(.*)/?', tornado.web.StaticFileHandler, {'path': 'uploads'}),
            (r'/ajax/remove/?', AjaxDeleteHandler),
            (r'/ajax/delete/?', AjaxDeletePassHandler),
            (r'/ajax/ban/?', AjaxBanHandler),
            (r'/ajax/report/?', AjaxReportHandler),
            (r'/ajax/info/?', AjaxInfoHandler),
            (r'/ajax/pin/?', AjaxPinHandler),
            (r'/ajax/lock/?', AjaxLockHandler),
            (r'/ajax/get/?', AjaxPostGetter),
            (r'/ajax/banner-del/?', AjaxBannerDelHandler),
            (r'/ajax/move/?', AjaxMoveHandler),
            (r'/ajax/infinify/?', AjaxInfinifyHandler),
            (r'/ajax/map/?', AjaxMapHandler),
        ]

        settings = {
            'ui_modules': uimodules,
            'template_path': 'templates',
            'static_path': 'static',
            'xsrf_cookies': True,
            'cookie_secret': "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        }

        self.con = motor.motor_tornado.MotorClient('localhost', 27017)
        self.database = self.con['imageboard']
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    check_path(uploads)
    check_path('banners/')
    tornado.options.parse_command_line()
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application, max_buffer_size=_ib.MAX_FILESIZE)
    http_server.listen(options.port)
    schedule_check(application)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

