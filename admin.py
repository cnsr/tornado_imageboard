import tornado.web
import datetime
import motor.motor_tornado
import ib_settings as _ib

from uuid import uuid4

from utils import *
from logger import log

# decorator that checks if user is admin
def ifadmin(f):
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            return self.redirect('/admin/login')
        return f(self, *args, **kwargs)
    return wrapper


# crappy handler that checks if user is admin
class LoggedInHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('adminlogin')


# login for admin; it's fucking awful since pass is in plaintext and that's only one of shitty things
# also cant use decorator here thus it's ugly as fuck
class AdminLoginHandler(LoggedInHandler):

    async def get(self):
        if not self.current_user:
            boards_list = await self.application.database.boards.find({}).to_list(None)
            self.render('admin_login.html', boards_list=boards_list)
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
        self.render('admin_stats.html', boards=boards, boards_list=boards_list, popup=popup)

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
        self.render('admin_banned.html', bans=bans, boards_list=boards_list)

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
        self.render('admin_reported.html', reports=reports, boards_list=boards_list)

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
            self.render('admin.html', boards_list=boards_list)


# creation of boards
class AdminBoardCreationHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        boards_list = await self.application.database.boards.find({}).to_list(None)
        self.render('admincreate.html', boards_list=boards_list)

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
        await db.insert(data)
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
            self.render('admin_edit.html', boards_list=boards_list, i=instance)
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
        #logs = await db.logs.find({}).sort('time', -1).to_list(None)[:5000]
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
            current = 0
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
        self.render('admin_logs.html', logs=logs, boards_list=boards_list, paged=paged, current=current)

    async def chunkify(self, l, n=30):
        res = list()
        for i in range(0, len(l), n):
            res.append(l[i:i + n])
        return res


