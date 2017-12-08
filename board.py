import tornado.options
import tornado.httpserver
import tornado.web
import tornado.ioloop
import pymongo
import uimodules
from datetime import datetime


from tornado.options import define, options
define('port', default=8000, help='run on given port', type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        db = self.application.database
        threads = db['posts'].find({'oppost': True}).sort([('_id', -1)]).limit(100)
        self.render('index.html', threads=threads)
    def post(self):
        db = self.application.database
        threads = db['posts'].find({'oppost': True}).sort([('_id', -1)]).limit(100)
        subject = self.get_argument('subject', '')
        text = self.get_argument('text', 'empty post')
        count = latest(db) + 1
        oppost = True
        thread = None
        data = makedata(subject, text, count, oppost, thread)
        db['posts'].insert(data)
        self.render('index.html', threads=threads)


class ThreadHandler(tornado.web.RequestHandler):
    thread_count = ''
    def get(self, count):
        thread_count = int(count)
        db = self.application.database
        posts = db['posts'].find({'thread': thread_count}).sort([('count', pymongo.ASCENDING)])
        op = db['posts'].find_one({"count": thread_count})
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
        db['posts'].insert(data)
        op = db['posts'].find_one({'count': thread_count})
        posts = db['posts'].find({'thread': thread_count}).sort([('count', pymongo.ASCENDING)])
        self.render('posts.html', op=op, posts=posts)


def makedata(subject, text, count, oppost=False, thread=None):
    data = {}
    data['subject'] = subject
    data['text'] = text
    data['count'] = count
    data['date'] = datetime.utcnow()
    data['oppost'] = oppost
    data['thread'] = thread
    return data


# this is an ugly hack that works somehow
# i need to read docs on pymongo cursor
def latest(db):
    try:
        return list(db['posts'].find({}).sort('count', -1))[0]['count']
    except Exception as e:
        print(e)
        return 0

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
        try:
            self.database.create_collection('posts', capped=True, size=10000)
        except pymongo.errors.CollectionInvalid:
            pass
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    tornado.options.parse_command_line()
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
