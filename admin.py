import tornado.web
import datetime
import motor.motor_tornado

from uuid import uuid4

from utils import *

# decorator that checks if user is admin
def ifadmin(f):
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            self.redirect('/admin/login')
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
        if password == _ib.ADMIN_PASS:
            self.set_secure_cookie('adminlogin', 'true')
            self.redirect('/admin')
        else:
            self.redirect('/')


class AdminLogoutHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        self.clear_cookie('adminlogin')
        self.redirect('/')


# stats of boards for admins
class AdminStatsHandler(LoggedInHandler):
    @ifadmin
    async def get(self):
        boards = await self.application.database.boards.find({}).to_list(None)
        boards_list = await self.application.database.boards.find({}).to_list(None)
        self.render('admin_stats.html', boards=boards, boards_list=boards_list)


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
        data['postcount'] = 0
        data['mediacount'] = 0
        data['created'] = datetime.datetime.utcnow()
        data['banners'] = []
        if self.request.files:
            f = self.request.files['banner'][0]
            ext = f['filename'].split('.')[-1]
            newname = 'banners/' + data['short'] + '-' + str(uuid4()).split('-')[-1] + '.' + ext
            with open(newname, 'wb') as nf:
                nf.write(bytes(f['body']))
            data['banners'].append(newname)
        db = self.application.database.boards
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
        if self.request.files:
            f = self.request.files['banner'][0]
            ext = f['filename'].split('.')[-1]
            newname = 'banners/' + instance['short'] + '-' + str(uuid4()).split('-')[-1] + '.' + ext
            with open(newname, 'wb') as nf:
                nf.write(bytes(f['body']))
            instance['banners'].append(newname)
        await self.application.database.boards.update_one({'short':board},{'$set':instance})
        self.redirect('/admin/stats/')

