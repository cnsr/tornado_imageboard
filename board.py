import tornado.options
import tornado.httpserver
import tornado.web
import tornado.ioloop
import pymongo
import uimodules
import datetime
import ib_settings as _ib
from tornado import concurrent

from tornado.options import define, options
define('port', default=8000, help='run on given port', type=int)

executor = concurrent.futures.ThreadPoolExecutor(8)

# should be remade to board handler
class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        db = self.application.database
        threads = db['posts'].find({'oppost': True}).sort([('lastpost', -1)]).limit(_ib.THREAD_NUMBER)
        self.render('index.html', threads=threads)

    def post(self):
        db = self.application.database
        threads = db['posts'].find({'oppost': True}).sort([('lastpost', -1)]).limit(_ib.THREAD_NUMBER)
        subject = self.get_argument('subject', '')
        text = self.get_argument('text', '')
        count = latest(db) + 1
        oppost = True
        thread = None
        data = makedata(subject, text, count, oppost, thread)
        # doesnt let to post without text
        if data['text'] != '':
            db['posts'].insert(data)
        self.render('index.html', threads=threads)


class ThreadHandler(tornado.web.RequestHandler):
    thread_count = ''

    def get(self, count):
        thread_count = int(count)
        db = self.application.database
        posts = db['posts'].find({'thread': thread_count}).sort([('count', pymongo.ASCENDING)])
        op = db['posts'].find_one({"count": thread_count})
        if check_thread(db, thread_count, _ib.THREAD_POSTS):
            op['locked'] = True
            update_db(db, op['count'], op)
        self.render('posts.html', op=op, posts=posts)

    def post(self, thread_count):
        thread_count = int(thread_count)
        db = self.application.database
        subject = self.get_argument('subject', '')
        text = self.get_argument('text', 'empty post')
        count = latest(db) + 1
        oppost = False
        thread = thread_count
        data = makedata(subject, text, count, oppost, thread)
        op = db['posts'].find_one({'count': thread_count})
        if not check_thread(db, thread_count, _ib.THREAD_BUMP):
            op['lastpost'] = datetime.datetime.utcnow()
            update_db(db, op['count'], op)
        if not op['locked']:
            db['posts'].insert(data)
        posts = db['posts'].find({'thread': thread_count}).sort([('count', pymongo.ASCENDING)])
        self.render('posts.html', op=op, posts=posts)


# constructs dictionary to insert into mongodb
def makedata(subject, text, count, oppost=False, thread=None):
    data = {}
    data['subject'] = subject
    data['text'] = text
    data['count'] = count
    data['date'] = datetime.datetime.utcnow()
    data['oppost'] = oppost
    data['thread'] = thread
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
            (r'/thread/(\d+)', ThreadHandler),
        ]

        settings = {
            'ui_modules': uimodules,
            'template_path': 'templates',
            'static_path': 'static',
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
        col = app.database.posts
        threads = col.find({'oppost': True}).sort('lastpost', 1)
        if not threads.count() <= _ib.THREAD_NUMBER:
            threads = threads.limit(threads.count() - _ib.THREAD_NUMBER)
            for thread in threads:
                col.delete_many({'thread': thread['count']})
                col.remove({'count': thread['count']})
            print('task finished')
    def wrapper():
        executor.submit(task)
        schedule_check(app)
    tornado.ioloop.IOLoop.current().add_timeout(next_time, wrapper)



def main():
    tornado.options.parse_command_line()
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    schedule_check(application)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
