import datetime
import re
from uuid import uuid4

import motor.motor_tornado
import tornado.web

import src.ib_settings as _ib
from src.logger import log
from src.utils import *


# crappy handler that checks if user is admin
class LoggedInHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('adminlogin')

    def check_origin(self, origin):
        return True

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')

    def options(self):
        self.set_status(204)
        self.finish()

# login for admin; it's fucking awful since pass is in plaintext and that's only one of shitty things
# also cant use decorator here thus it's ugly as fuck
class AdminLoginHandler(LoggedInHandler):

    async def get(self):
        if not self.current_user:
            boards_list = await self.application.database.boards.find({}).to_list(None)
            self.render('admin/admin_login.html', boards_list=boards_list)
        else:
            self.redirect('/admin')
            return

    async def post(self):
        password = self.get_argument('password')
        ip = await get_ip(self.request)
        if password == _ib.ADMIN_PASS:
            self.set_secure_cookie('adminlogin', 'true')
            log_message = '{0} has logged in as admin'.format(ip)
            await log('other', log_message)
            self.redirect('/admin')
        else:
            log_message = '{0} has attempted to log in as admin'.format(ip)
            await log('other', log_message)
            self.redirect('/')


class AdminLogoutHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        self.clear_cookie('adminlogin')
        ip = await get_ip(self.request)
        log_message = '{0} has logged in as admin'.format(ip)
        await log('other', log_message)
        self.redirect('/')


# stats of boards for admins
class AdminStatsHandler(LoggedInHandler):
    responses = {'success':'Deletion successful.',
                'error': 'Board does not exist.'}
    @ifadmin
    async def get(self):
        popup = None
        if self.get_arguments('msg') != []:
            msg = self.get_argument('msg')
            popup = self.responses.get(msg)
        boards = await self.application.database.boards.find({}).to_list(None)
        boards_list = await self.application.database.boards.find({}).to_list(None)
        self.render('admin', boards=boards, boards_list=boards_list, popup=popup)

    @ifadmin
    async def post(self):
        short = self.get_argument('short')
        board = await self.application.database.boards.find_one({'short': short})
        url = self.request.uri.split('?')[0]
        if board:
            try:
                posts = await self.application.database.posts.find({'board': board['short']}).to_list(None)
                for post in posts:
                    await removeing(post)
                    await self.application.database.posts.delete_one({'count': post['count']})
                log_message = 'Board {0} has been deleted.'.format(board['short'])
                await log('board_remove', log_message)
                await self.application.database.boards.delete_one({'short':short})
                self.redirect(url + '?msg=success')
            except:
                self.redirect(url + '?msg=error1')
        else:
            self.redirect(url + '?msg=error')


# you can view bans here
class AdminBannedHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        db = self.application.database
        bans = await db.bans.find({}).sort([('date', 1)]).to_list(None)
        boards_list = await db.boards.find({}).to_list(None)
        self.render('admin/admin_banned.html', bans=bans, boards_list=boards_list)

    @ifadmin
    async def post(self):
        db = self.application.database
        ip = self.get_argument('ip')
        await db.bans.delete_one({'ip': ip})
        log_message = '{0} was unbanned by admin.'.format(ip)
        await log('unban', log_message)
        self.redirect('/admin/bans')


# you can view reports here
class AdminReportsHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        db = self.application.database
        reports = await db.reports.find({}).sort([('date', 1)]).to_list(None)
        boards_list = await db.boards.find({}).to_list(None)
        self.render('admin/admin_reported.html', reports=reports, boards_list=boards_list)

    @ifadmin
    async def post(self):
        db = self.application.database
        ip = self.get_argument('ip')
        if ip != 'all':
            await db.reports.delete_one({'ip': ip})
        else:
            await db.reports.remove({})
        self.redirect('/admin/reports')


# admin main page
class AdminHandler(LoggedInHandler):

    async def get(self):
        if not self.current_user:
            self.redirect('/admin/login')
        else:
            boards_list = await self.application.database.boards.find({}).to_list(None)
            self.render('admin/admin.html', boards_list=boards_list)


# creation of boards
class AdminBoardCreationHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        boards_list = await self.application.database.boards.find({}).to_list(None)
        self.render('admin/admincreate.html', boards_list=boards_list)

    @ifadmin
    async def post(self):
        data = {}
        data['name'] = self.get_argument('name', '')
        data['short']= self.get_argument('short', '')
        data['username'] = self.get_argument('username', '')
        data['description'] = self.get_argument('description', '')
        data['thread_posts'] = int(self.get_argument('thread_posts', ''))
        data['thread_bump'] = int(self.get_argument('thread_bump', ''))
        data['thread_catalog'] = int(self.get_argument('thread_catalog', ''))
        data['country'] = 'country' in self.request.arguments
        data['custom'] = 'custom' in self.request.arguments
        data['roll'] = 'roll' in self.request.arguments
        data['unlisted'] = 'unlisted' in self.request.arguments
        data['postcount'] = 0
        data['mediacount'] = 0
        data['created'] = datetime.datetime.utcnow()
        data['banners'] = []
        data['perpage'] = int(float(self.get_argument('perpage', 10)))
        data['pinned'] = None
        if self.request.files:
            f = self.request.files['banner'][0]
            ext = f['filename'].split('.')[-1]
            newname = 'banners/' + data['short'] + '-' + str(uuid4()).split('-')[-1] + '.' + ext
            with open(newname, 'wb') as nf:
                nf.write(bytes(f['body']))
            data['banners'].append(newname)
        db = self.application.database.boards
        log_message = 'Board /{0}/ has been created.'.format(data['short'])
        await log('board_creation', log_message)
        await db.insert_one(data)
        self.redirect('/' + data['short'])


# editing existing boards
class AdminBoardEditHandler(LoggedInHandler):
    @ifadmin
    async def get(self, board):
        instance = await self.application.database.boards.find_one({'short': board})
        if instance:
            to_remove = ['postcount', 'mediacount', 'created']
            for key in to_remove:
                if key in instance:
                    del instance[key]
            boards_list = await self.application.database.boards.find({}).to_list(None)
            self.render('admin/admin_edit.html', boards_list=boards_list, i=instance)
        else:
            self.redirect('/admin/stats')

    @ifadmin
    async def post(self, board):
        instance = await self.application.database.boards.find_one({'short': board})
        instance['name'] = self.get_argument('name', '')
        instance['short']= self.get_argument('short', '')
        instance['username'] = self.get_argument('username', '')
        instance['description'] = self.get_argument('description', '')
        instance['thread_posts'] = int(self.get_argument('thread_posts', ''))
        instance['thread_bump'] = int(self.get_argument('thread_bump', ''))
        instance['thread_catalog'] = int(self.get_argument('thread_catalog', ''))
        instance['country'] = 'country' in self.request.arguments
        instance['custom'] = 'custom' in self.request.arguments
        instance['roll'] = 'roll' in self.request.arguments
        instance['unlisted'] = 'unlisted' in self.request.arguments
        instance['perpage'] = int(float(self.get_argument('perpage', 10)))
        pinned = 'pinned' in self.request.arguments
        if not pinned:
            instance['pinned'] = None
        if self.request.files:
            f = self.request.files['banner'][0]
            ext = f['filename'].split('.')[-1]
            newname = 'banners/' + instance['short'] + '-' + str(uuid4()).split('-')[-1] + '.' + ext
            with open(newname, 'wb') as nf:
                nf.write(bytes(f['body']))
            instance['banners'].append(newname)
        log_message = 'Board /{0}/ has been edited.'.format(instance['short'])
        await log('board_edit', log_message)
        await self.application.database.boards.update_one({'short':board},{'$set':instance})
        self.redirect('/admin/stats/')


# you can view logs here
class AdminLogsHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        db = self.application.database
        log_types = ['post', 'post_remove', 'board_creation', 'board_edit', 'board_remove', 'ban', 'unban', 'other',]
        log_type = self.get_argument('type', 'all', False)
        current = 0
        if not log_type:
            #logs = await db.logs.find({}).sort('time', -1).to_list(None)[:5000]
            logs = await db.log.find({}).sort('time', -1).to_list(None) or None
        else:
            if log_type != 'all':
                if log_type in log_types:
                    logs = await db.log.find({'type': log_type}).sort('time', -1).to_list(None) or None
                else: logs = await db.log.find({}).sort('time', -1).to_list(None) or None
            else:
                logs = await db.log.find({}).sort('time', -1).to_list(None) or None
        if logs:
            if self.get_arguments('page') != []:
                try:
                    page = int(self.get_argument('page'))
                except ValueError:
                    page = 0
            else:
                page = 0
            _logs = await self.chunkify(logs)
            try:
                logs = _logs[page]
            except IndexError:
                try:
                    logs = _logs[0]
                except IndexError:
                    pass
            if len(_logs) > 1:
                paged = []
                url = self.request.uri.split('?')[0]
                for x in range(len(_logs)):
                    paged.append({
                        'numb': x,
                        'url': url + '?page=' + str(x),
                    })
                    if x == page:
                        current = x
            else:
                paged = None
        else:
            paged = None
        boards_list = await db.boards.find({}).to_list(None)
        self.render('admin/admin_logs.html', logs=logs, boards_list=boards_list, paged=paged, current=current,
        log_types=log_types, curr_type=log_type)

    async def chunkify(self, l, n=30):
        res = list()
        for i in range(0, len(l), n):
            res.append(l[i:i + n])
        return res


class AdminBlackListHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        db = self.application.database
        blacklist = get_blacklist()
        boards_list = await db.boards.find({}).to_list(None)
        self.render('admin/admin_blacklist.html', boards_list=boards_list, blacklist=blacklist)

    @ifadmin
    async def post(self):
        blacklist = get_blacklist()
        del_word = self.get_argument('delete', '')
        if del_word:
            blacklist.remove(del_word)
            save_blacklist(blacklist)
            self.redirect('/admin/blacklist/')
        else:
            words = self.get_argument('words', '')
            words = words.split(',')
            words = [word.strip().lower() for word in words]
            blacklist += words
            save_blacklist(blacklist)
            self.redirect('/admin/blacklist/')


class AdminIPSearchHandler(LoggedInHandler):
    responses = {'success':'Successfully banned',
                'error': 'No posts were found',
                'nop': 'Error banning IP'}
    @ifadmin
    async def get(self, count):
        # TODO: show whether IP has any bans
        popup = None
        if self.get_arguments('msg') != []:
            msg = self.get_argument('msg')
            popup = self.responses.get(msg)
        boards = await self.application.database.boards.find({}).to_list(None)
        boards_list = await self.application.database.boards.find({}).to_list(None)
        post = await self.application.database.posts.find_one({'count': int(count)}) or None
        banned = await self.application.database.bans.find_one({'ip': post['ip']}) or None
        if post:
            posts_by_same_ip = await self.application.database.posts.find({'ip': post['ip']}).sort('date', -1).to_list(None)
            self.render('admin/admin_search.html', boards=boards,
                        boards_list=boards_list, popup=popup,
                        posts=posts_by_same_ip, count=count,
                        banned=banned)
        else:
            self.redirect('/admin/')

    # TODO: add deletion that keeps the post list upon page update
    @ifadmin
    async def post(self, count):
        action = self.get_argument('action')
        post = await self.application.database.posts.find_one({'count': int(count)}) or None
        if post:
            if action == 'ban':
                banned = await self.application.database.bans.find_one({'ip': post['ip']})
                if not banned:
                    ban = {
                        'ip': post['ip'],
                        'ban_post': int(post['count']),
                        'reason': 'Banned after reviewing post history',
                        'locked': False,
                        'date': None,
                        'date_of': datetime.datetime.utcnow(),
                    }
                    if not post['oppost']:
                        ban['url'] = '/' + post['board'] + '/thread/' + str(post['thread']) + '#' + str(post['count'])
                    else:
                        ban['url'] = '/' + post['board'] + '/thread/' + str(post['count']) + '#' + str(post['count'])
                    log_message = '{0} was banned for post #{1} (unban {2}).'.format(post['ip'], post['count'], ban['date'])
                    await log('ban', log_message)
                    await self.application.database.bans.insert_one(ban)
                    post['banned'] = True
                    await update_db(self.application.database, post['count'], post)
        else:
            self.redirect('/admin/search' + count +'?msg=nop')
        self.redirect('/admin/search/' + count + '/')



