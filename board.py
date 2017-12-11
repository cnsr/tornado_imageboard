import tornado.options
import tornado.httpserver
import tornado.web
import tornado.ioloop
import pymongo
import uimodules
import datetime
import ib_settings as _ib
from tornado import concurrent
import re

from tornado.options import define, options
define('port', default=8000, help='run on given port', type=int)

executor = concurrent.futures.ThreadPoolExecutor(8)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        boards = self.application.database.boards.find({})
        boards_list = self.application.database.boards.find({})
        self.render('index.html', boards=boards, boards_list=boards_list)


class BoardHandler(tornado.web.RequestHandler):

    def get(self, board):
        db = self.application.database
        threads = db['posts'].find({'board': board,'oppost': True}).sort([('lastpost', -1)]).limit(_ib.THREAD_NUMBER)
        db_board = db.boards.find({'short': board})
        boards_list = self.application.database.boards.find({})
        self.render('board.html', threads=threads, board=db_board, boards_list=boards_list)

    def post(self, board):
        db = self.application.database
        threads = db['posts'].find({'board': board,'oppost': True}).sort([('lastpost', -1)]).limit(_ib.THREAD_NUMBER)
        subject = self.get_argument('subject', '')
        text = self.get_argument('text', '')
        text = text.replace("\n","<br />\n")
        result = linkify(text)
        text = result[0]
        count = latest(db) + 1
        oppost = True
        thread = None
        data = makedata(subject, text, count, board, oppost, thread)
        db['posts'].insert(data)
        db_board = db.boards.find({'short': board})
        # self.render('board.html', threads=threads, board=db_board)
        self.redirect('/' + board + '/thread/' + str(data['count']))


class ThreadHandler(tornado.web.RequestHandler):
    thread_count = ''

    def get(self, board, count):
        thread_count = int(count)
        db = self.application.database
        posts = db['posts'].find({'thread': thread_count}).sort([('count', pymongo.ASCENDING)])
        op = db['posts'].find_one({"count": thread_count})
        if check_thread(db, thread_count, _ib.THREAD_POSTS):
            op['locked'] = True
            update_db(db, op['count'], op)
        db_board = db.boards.find({'short': board})
        boards_list = self.application.database.boards.find({})
        self.render('posts.html', op=op, posts=posts, board=db_board, boards_list=boards_list)

    def post(self, board, thread_count):
        thread_count = int(thread_count)
        db = self.application.database
        subject = self.get_argument('subject', '')
        text = self.get_argument('text', 'empty post')
        result = linkify(text)
        text = result[0]
        text = text.replace("\n","<br />\n")
        replies = result[1]
        count = latest(db) + 1
        oppost = False
        thread = thread_count
        data = makedata(subject, text, count, board, oppost, thread)
        op = db['posts'].find_one({'count': thread_count})
        if not check_thread(db, thread_count, _ib.THREAD_BUMP):
            op['lastpost'] = datetime.datetime.utcnow()
            update_db(db, op['count'], op)
        if not op['locked']:
            if data['text'] != '':
                db['posts'].insert(data)
                for number in replies:
                    p = db.posts.find_one({'count': int(number)})
                    old_replies = p['replies']
                    if int(data['count']) not in old_replies:
                        old_replies.append(int(data['count']))
                        p['replies'] = old_replies
                        update_db(db, p['count'], p)
        posts = db['posts'].find({'thread': thread_count}).sort([('count', pymongo.ASCENDING)])
        db_board = db.boards.find({'short': board})
        boards_list = self.application.database.boards.find({})
        self.render('posts.html', op=op, posts=posts, board=db_board, boards_list=boards_list)


class LoggedInHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('adminlogin')


class AdminHandler(LoggedInHandler):

    def get(self):
        if not self.current_user:
            self.redirect('/admin/login')
            return
        else:
            boards_list = self.application.database.boards.find({})
            self.render('admin.html', boards_list=boards_list)

    def post(self):
        if self.current_user:
            data = {}
            data['name'] = self.get_argument('name', '')
            data['short']= self.get_argument('short', '')
            data['description'] = self.get_argument('description', '')
            db = self.application.database.boards
            db.insert(data)
            self.redirect('/' + data['short'])


class AdminLoginHandler(LoggedInHandler):

    def get(self):
        if not self.current_user:
            boards_list = self.application.database.boards.find({})
            self.render('admin_login.html', boards_list=boards_list)
        else:
            self.redirect('/admin')
            return

    def post(self):
        password = self.get_argument('password')
        if password == _ib.ADMIN_PASS:
            self.set_secure_cookie('adminlogin', 'true')
            self.redirect('/admin')
        else:
            self.redirect('/')

# constructs dictionary to insert into mongodb
def makedata(subject, text, count, board, oppost=False, thread=None):
    data = {}
    data['subject'] = subject
    data['text'] = text
    data['count'] = count
    data['board'] = board
    data['date'] = datetime.datetime.utcnow()
    data['oppost'] = oppost
    data['thread'] = thread
    data['replies'] = []
    if oppost:
        data['locked'] = False
        data['lastpost'] = datetime.datetime.utcnow()
    return data


# this is an ugly hack that works somehow
# i need to read docs on pymongo cursor
def latest(db):
    try:
        return list(db['posts'].find({}).sort('count', -1))[0]['count']
    except Exception as e:
        print(e)
        return 0


# checks if number of posts in thread exceeds whatever number you check it against
def check_thread(db, thread, subj):
    return db.posts.find({'thread': thread}).count() >= subj


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/', IndexHandler),
            (r'/(\w+)', BoardHandler),
            (r'/(\w+)/thread/(\d+)', ThreadHandler),
            (r'/admin/', AdminHandler),
            (r'/admin/login', AdminLoginHandler),
        ]

        settings = {
            'ui_modules': uimodules,
            'template_path': 'templates',
            'static_path': 'static',
            'xsrf_cookies': True,
            'cookie_secret': "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        }

        self.con = pymongo.MongoClient('localhost', 27017)
        self.database = self.con['imageboard']
        tornado.web.Application.__init__(self, handlers, **settings)


# updates one db entry by set parametres
def update_db(db, count, variables):
    db.posts.update_one(
        {'count': count},
        {
            '$set': variables
        }
    )


# deletes the threads that are inactive after there are too much threads
def schedule_check(app):
    next_time = datetime.timedelta(0, _ib.CHECK_TIMEOUT)
    def task():
        # delete all threads except first N, sorted by bumps
        db = app.database
        boards = db.boards.find({})
        for board in boards:
            threads = db.posts.find({'oppost': True, 'board': board['short']}).sort('lastpost', 1)
            if not threads.count() <= _ib.THREAD_NUMBER:
                threads = threads.limit(threads.count() - _ib.THREAD_NUMBER)
                for thread in threads:
                    col.delete_many({'thread': thread['count']})
                    col.remove({'count': thread['count']})
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
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    schedule_check(application)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
