import tornado.options
import tornado.httpserver
import tornado.web
import tornado.ioloop
import pymongo
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

from tornado.options import define, options
define('port', default=8000, help='run on given port', type=int)

executor = concurrent.futures.ThreadPoolExecutor(8)

uploads = 'uploads/'


class IndexHandler(tornado.web.RequestHandler):
    async def get(self):
        db = self.application.database
        boards = await db.boards.find({}).to_list(None)
        boards_list = await db.boards.find({}).to_list(None)
        self.render('index.html', boards=boards, boards_list=boards_list)


class BoardHandler(tornado.web.RequestHandler):

    async def get(self, board):
        board = board.split('/')[0]
        db = self.application.database
        db_board = await db.boards.find_one({'short': board})
        if db_board:
            threads = await db['posts'].find({'board': board,'oppost': True}).sort([('lastpost', -1)]).limit(db_board['thread_catalog']).to_list(None)
            boards_list = await db.boards.find({}).to_list(None)
            self.render('board.html', threads=threads, board=db_board, boards_list=boards_list)
        else:
            self.redirect('/')

    async def post(self, board):
        db = self.application.database
        db_board = await db.boards.find_one({'short': board})
        threads = await db['posts'].find({'board': board,'oppost': True}).sort([('lastpost', -1)]).limit(db_board['thread_catalog']).to_list(None)
        subject = self.get_argument('subject', '')
        text = self.get_argument('text', '')
        text = text.replace("\n","<br />\n")
        if self.request.files:
            file, filetype = await upload_file(self.request.files['file'][0])
        else:
            file = filetype = None
        result = linkify(text)
        text = result[0]
        count = await latest(db) + 1
        oppost = True
        thread = None
        data = await makedata(db, subject, text, count, board, oppost, thread, file, filetype)
        await db['posts'].insert(data)
        self.redirect('/' + board + '/thread/' + str(data['count']))


class ThreadHandler(tornado.web.RequestHandler):
    thread_count = ''

    async def get(self, board, count):
        thread_count = int(count)
        db = self.application.database
        db_board = await db.boards.find_one({'short': board})
        posts = await db['posts'].find({'thread': thread_count}).sort([('count', pymongo.ASCENDING)]).to_list(None)
        op = await db['posts'].find_one({"count": thread_count})
        if op != None:
            if await check_thread(db, thread_count, db_board['thread_posts']):
                op['locked'] = True
                await update_db(db, op['count'], op)
            boards_list = await db.boards.find({}).to_list(None)
            self.render('posts.html', op=op, posts=posts, board=db_board, boards_list=boards_list)
        else:
            self.redirect('/' + board)

    async def post(self, board, thread_count):
        thread_count = int(thread_count)
        db = self.application.database
        subject = self.get_argument('subject', '')
        text = self.get_argument('text', 'empty post')
        result = linkify(text)
        text = result[0]
        text = text.replace("\n","<br />\n")
        if self.request.files:
            file, filetype = await upload_file(self.request.files['file'][0])
        else:
            file = filetype = None
        replies = result[1]
        count = await latest(db) + 1
        oppost = False
        thread = thread_count
        data = await makedata(db, subject, text, count, board, oppost, thread, file, filetype)
        op = await db['posts'].find_one({'count': thread_count})
        db_board = await db.boards.find_one({'short': board})
        if not op['locked']:
            if not await check_thread(db, thread_count, db_board['thread_bump']):
                if not data['subject'] == 'sage':
                    op['lastpost'] = datetime.datetime.utcnow()
                    await update_db(db, op['count'], op)
            await db.posts.insert(data)
            for number in replies:
                p = await db.posts.find_one({'count': int(number)})
                old_replies = p['replies']
                if int(data['count']) not in old_replies:
                    old_replies.append(int(data['count']))
                    p['replies'] = old_replies
                    await update_db(db, p['count'], p)
        posts = await db['posts'].find({'thread': thread_count}).sort([('count', pymongo.ASCENDING)]).to_list(None)
        boards_list = await db.boards.find({}).to_list(None)
        if op != None:
            self.render('posts.html', op=op, posts=posts, board=db_board, boards_list=boards_list)
        else:
            self.redirect('/' + board)



async def upload_file(file):
    fname = file['filename']
    fext = os.path.splitext(fname)[1]
    if fext in ['.jpg', 'gif', '.png','.jpeg']:
        filetype = 'image'
    elif fext in ['.webm', '.mp4']:
        filetype = 'video'
    else:
        return None, None
    newname = uploads + str(uuid4()) + fext
    with open(newname, 'wb') as f:
        f.write(bytes(file['body']))
    return newname, filetype


class AjaxFileHandler(tornado.web.RequestHandler):

    async def post(self):
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        response = await self.construct(data)
        self.write(json.dumps(response))

    def convert_bytes(self, num):
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0

    async def construct(self, data):
        file = data['image'].decode('utf-8')[1:]
        if os.path.isfile(file):
            filesize = self.convert_bytes((os.stat(file).st_size))
            response = {'status': 'ok',
                        'file': file.split('/')[1],
                        'filesize': filesize,
                        'fileext': file.split('.')[1],
            }
            if file.endswith(('webm', 'mp4')):
                w,h = resolution(file)
                response['w'] = w
                response['h'] = h
        else:
            response = {'status': 'not ok'}
        return response


class LoggedInHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('adminlogin')


class AdminHandler(LoggedInHandler):

    async def get(self):
        if not self.current_user:
            self.redirect('/admin')
        else:
            boards_list = await self.application.database.boards.find({}).to_list(None)
            self.render('admin.html', boards_list=boards_list)


class AdminBoardCreationHandler(LoggedInHandler):

    async def get(self):
        if not self.current_user:
            self.redirect('/admin/login')
            # return
        else:
            boards_list = await self.application.database.boards.find({}).to_list(None)
            self.render('admincreate.html', boards_list=boards_list)

    async def post(self):
        if self.current_user:
            data = {}
            data['name'] = self.get_argument('name', '')
            data['short']= self.get_argument('short', '')
            data['username'] = self.get_argument('username', '')
            data['description'] = self.get_argument('description', '')
            data['thread_posts'] = int(self.get_argument('thread_posts', ''))
            data['thread_bump'] = int(self.get_argument('thread_bump', ''))
            data['thread_catalog'] = int(self.get_argument('thread_catalog', ''))
            data['postcount'] = 0
            data['mediacount'] = 0
            db = self.application.database.boards
            await db.insert(data)
            self.redirect('/' + data['short'])


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

# constructs dictionary to insert into mongodb
async def makedata(db, subject, text, count, board, oppost=False, thread=None, file=None, filetype=None):
    data = {}
    data['subject'] = subject
    data['text'] = text
    data['count'] = count
    data['board'] = board
    data['date'] = datetime.datetime.utcnow()
    data['oppost'] = oppost
    data['thread'] = thread
    data['replies'] = []
    b = await db.boards.find_one({'short': board})
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
    else:
        postcount = await db.posts.find({'thread': t['count']}).count()
        t['postcount'] = postcount + 1
    if file:
        b['filecount'] = b['filecount'] + 1
        if filetype == 'image':
            data['image'] = file
            data['video'] = None
        else:
            data['video'] = file
            data['image'] = None
        if not oppost:
            filecount = await db.posts.find({'thread': t['count'],
                                        'image': { '$ne': None }
                                        }).count() + await db.posts.find({'thread': t['count'],
                                                                    'video': {'$ne': None}}).count()
            t['filecount'] = filecount + 1
            await update_db(db, t['count'], t)
    else:
        data['image'] = data['video'] = None
    b['postcount'] = b['postcount'] + 1
    await update_db_b(db, b['short'], b)
    return data


# this is an ugly hack that works somehow
# i need to read docs on pymongo cursor
async def latest(db):
    try:
        return list(await db['posts'].find({}).sort('count', -1).to_list(None))[0]['count']
    except Exception as e:
        print(e)
        return 0


# checks if number of posts in thread exceeds whatever number you check it against
async def check_thread(db, thread, subj):
    return await db.posts.find({'thread': thread}).count() >= subj


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/$', IndexHandler),
            (r'/admin/?', AdminHandler),
            (r'/(\w+)/?', BoardHandler),
            (r'/(\w+)/thread/(\d+)/?', ThreadHandler),
            (r'/admin/login/?', AdminLoginHandler),
            (r'/admin/create/?', AdminBoardCreationHandler),
            (r'/uploads/(.*)/?', tornado.web.StaticFileHandler, {'path': 'uploads'}),
            (r'/ajax/file/?', AjaxFileHandler),
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


# updates one db entry by set parametres
async def update_db(db, count, variables):
    await db.posts.update_one(
        {'count': count},
        {
            '$set': variables
        }
    )


# for updating board data
async def update_db_b(db, short, variables):
    await db.boards.update_one(
        {'short': short},
        {
            '$set': variables
        }
    )


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
                                        'board': board['short']}).sort('lastpost', pymongo.ASCENDING).to_list(None)
                if not len(threads) <= board['thread_catalog']:
                    threads = threads[:(threads.count(None) - board['thread_catalog'])]
                    for thread in threads:
                        if thread['video']:
                            os.remove(thread['video'])
                        if thread['image']:
                            os.remove(thread['image'])
                        posts = yield db.posts.find({'thread': thread['count']}).to_list(None)
                        for post in posts:
                            if post['video']:
                                os.remove(post['video'])
                            if post['image']:
                                os.remove(post['image'])
                        yield db.posts.delete_many({'thread': thread['count']})
                        yield db.posts.remove({'count': thread['count']})
        except Exception as e:
            print(e)
    def wrapper():
        executor.submit(task)
        schedule_check(app)
    tornado.ioloop.IOLoop.current().add_timeout(next_time, wrapper)


def linkify(text):
    new_text = []
    replies = []
    text_list = re.split(r'(\s+)', text)
    for t in text_list:
        x = re.compile(r'(>>\d+)').match(t)
        if x:
            number = x.group(1)
            replies.append(number[2:])
            t = re.sub(r'>>\d+', '<a href=\"#' + number[2:] + '\">' + number + '</a>', t)
        new_text.append(t)
    return (' ').join(new_text), replies


def main():
    tornado.options.parse_command_line()
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application, max_buffer_size=_ib.MAX_FILESIZE)
    http_server.listen(options.port)
    schedule_check(application)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
