import tornado.web
import json
import datetime
import motor.motor_tornado

from utils import *
from logger import log


# crappy handler that checks if user is admin
class LoggedInHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('adminlogin')


# delete posts using ajax
class AjaxDeleteHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        pid = int(data['post'].decode('utf-8'))
        post = await db.posts.find_one({'count': pid})
        if post:
            replies_to = await db.posts.find({'replies': {'$in': [pid]}}).to_list(None)
            for reply in replies_to:
                reply['replies'].remove(pid)
                await update_db(db, reply['count'], reply)
            response = {}
            if post['oppost']:
                posts = await db.posts.find({'thread': post['count']}).to_list(None)
                for post in posts:
                    await removeing(post)
                    await db.posts.delete_one({'count': post['count']})
                response['op'] = 'true'
            await removeing(post)
            if post['oppost']:
                log_message = 'Thread #{0} has been removed by admin'.format(pid)
            else:
                log_message = 'Post #{0} has been removed by admin'.format(pid)
            await log('post_remove', log_message)
            await db.posts.delete_one({'count': pid})
            response['status'] = ['deleted']
        else:
            response = {'status': 'Error deleting post.'}
        self.write(json.dumps(response))


# reporting users using ajax, doesnt need admin check
class AjaxReportHandler(tornado.web.RequestHandler):

    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        p = await db.posts.find_one({'count': int(data['post'])}, {'_id': False})
        report = {
            'ip': p['ip'],
            'post': int(data['post']),
            'reason': data['reason'],
            'date': datetime.datetime.utcnow(),
        }
        if not p['oppost']:
            report['url'] = '/' + p['board'] + '/thread/' + str(p['thread']) + '#' + str(p['count'])
        else:
            report['url'] = '/' + p['board'] + '/thread/' + str(p['count']) + '#' + str(p['count'])
        log_message = 'Report has been sent for post #{0} with ip {1}.'.format(p['count'], p['ip'])
        await log('post_remove', log_message)
        await db.reports.insert_one(report)
        response = {'ok': 'ok'}
        self.write(json.dumps(response))


# gives info about post
class AjaxInfoHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        p = await db.posts.find_one({'count': int(data['post'])}, {'_id': False})
        if p:
            p['date'] = p['date'].strftime("%Y-%m-%d %H:%M:%S")
            if p.get('lastpost', ''):
                p['lastpost'] = p['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
            self.write(json.dumps(p, indent=4, ensure_ascii=False))
        else:
            self.write(json.dumps({'error': 'post does not exist. perhaps, it has been deleted?'}))


# pins threads
class AjaxThreadPinHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        pst = data['post']
        # heard that eval is weak shit
        for b in eval(data['boards']):
            brd = await db.boards.find_one({'short': b})
            brd['pinned'] = pst
            await update_db_b(db, b, brd)
        self.write(json.dumps({'status':'ok'}))


# pins the threads so they appear first in query
class AjaxPinHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        thread = await db.posts.find_one({'count': int(data['post'])})
        if thread['oppost']:
            thread['pinned'] = not thread['pinned']
            await update_db(db, thread['count'], thread)
            self.write(json.dumps({'status':'ok'}))
        else:
            self.write(json.dumps({'status':'failed'}))


# threads are infinite:
# first in - first out,
# posts get deleted when they go beyond thread post limit
class AjaxInfinifyHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        thread = await db.posts.find_one({'count': int(data['post'])})
        if thread['oppost']:
            thread['infinite'] = not thread['infinite']
            await update_db(db, thread['count'], thread)
            self.write(json.dumps({'status':'ok'}))
        else:
            self.write(json.dumps({'status':'failed'}))


# locks the threads so that they can't be posted in
class AjaxLockHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        print(self.current_user)
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        thread = await db.posts.find_one({'count': int(data['post'])})
        if thread['oppost']:
            thread['locked'] = not thread['locked']
            await update_db(db, thread['count'], thread)
            self.write(json.dumps({'status':'ok'}))
        else:
            self.write(json.dumps({'status':'failed'}))


# deletion of banners
class AjaxBannerDelHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        brd = await db.boards.find_one({'short': data['brd']})
        banner = data['banner']
        if banner in brd['banners']:
            brd['banners'].remove(banner)
            await update_db_b(db, brd['short'], brd)
            os.remove(banner)
            self.write(json.dumps({'status':'ok'}))
        else:
            self.write(json.dumps({'status':'failed'}))


# banning users
class AjaxBanHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        response = {'ok': 'Banned'}
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        p = await db.posts.find_one({'count': int(data['post'])})
        banned = await db.bans.find_one({'ip': p['ip']})
        if not banned:
            ban = {
                'ip': p['ip'],
                'ban_post': int(data['post']),
                'reason': data['reason'],
                'locked': False,
                'date': None,
                'date_of': datetime.datetime.utcnow(),
            }
            if data['lock'] == 'true':
                ban['locked'] = True
            if data['date'] != 'Never':
                ban['date'] = data['date']
            if not p['oppost']:
                ban['url'] = '/' + p['board'] + '/thread/' + str(p['thread']) + '#' + str(p['count'])
            else:
                ban['url'] = '/' + p['board'] + '/thread/' + str(p['count']) + '#' + str(p['count'])
            log_message = '{0} was banned for post #{1} (unban {2}).'.format(p['ip'], p['count'], ban['date'])
            await log('unban', log_message)
            await db.bans.insert_one(ban)
            p['banned'] = True
            if ban['locked'] and p['oppost']:
                p['locked'] = True
            await update_db(db, p['count'], p)
            if data['rm'] == 'true':
                if p['oppost']:
                    posts = await db.posts.find({'thread': p['count']}).to_list(None)
                    for subp in posts:
                        await removeing(subp)
                    await db.posts.delete_many({'thread': p['count']})
                await removeing(p)
                await db.posts.delete_one({'count': p['count']})
        # TODO: make so it only updates the ban info and keep the post deletion/locking unchanged
        else:
            if data['date'] != 'Never':
                banned['date'] = data['date']
            else:
                banned['date'] = None
            banned['date_of'] = datetime.datetime.utcnow()
            await db.bans.update_one({'ip': banned['ip']}, {"$set": banned}, upsert=False)
            p['banned'] = True
            await update_db(db, p['count'], p)
        self.write(json.dumps(response))


# gets posts that have been posted since user loaded the page
class AjaxNewHandler(tornado.web.RequestHandler):

    async def post(self, board, thread):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        try:
            pid = int(data['latest'].decode('utf-8'))
            post = await db.posts.find_one({'count': pid})
            posts = await db.posts.find({'thread': int(thread)}).to_list(None)
            response = []
            for post in posts:
                if int(post['count']) <= pid:
                    del post
                else:
                    del post['_id']
                    del post['ip']
                    post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
                    post['text'] = ('').join(post['text'].split('<br />'))
                    post['isop'] = post.pop('op')
                    response.append(post)
            self.write(json.dumps(response))
        except KeyError:
            posts = await db.posts.find({'thread': int(thread)}).to_list(None)
            for post in posts:
                del post['_id']
                del post['ip']
                post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
            self.write(json.dumps(posts))


# delete posts using ajax if password is correct
# therefore, doesn't need admin check
class AjaxDeletePassHandler(tornado.web.RequestHandler):

    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        pid = int(data['post'].decode('utf-8'))
        password = data['password'].decode('utf-8')
        post = await db.posts.find_one({'count': pid})
        if post['pass'] == password:
            response = {}
            replies_to = await db.posts.find({'replies': {'$in': [pid]}}).to_list(None)
            for reply in replies_to:
                reply['replies'].remove(pid)
                await update_db(db, reply['count'], reply)
            if post['oppost']:
                posts = await db.posts.find({'thread': post['count']}).to_list(None)
                for post in posts:
                    await removeing(post)
                    await db.posts.delete_one({'count': post['count']})
                response['op'] = 'true'
            await removeing(post)
            if post['oppost']:
                log_message = 'Thread #{0} has been removed by {1}'.format(pid, post['ip'])
            else:
                log_message = 'Post #{0} has been removed by {1}'.format(pid, post['ip'])
            await log('post_remove', log_message)
            await db.posts.delete_one({'count': pid})
            response['status'] = 'deleted'
            self.write(json.dumps(response))
        else:
            self.write(json.dumps({'status': 'passwords do not match'}))


# loads the post from same or different threads on mouseover
class AjaxPostGetter(tornado.web.RequestHandler):

    async def post(self):
        result = {}
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        pid = int(data['post'].decode('utf-8'))
        post = await db.posts.find_one({'count': pid})
        if post:
            result['status'] = 'success'
            del post['_id']
            del post['ip']
            del post['pass']
            post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
            if post.get('lastpost'):
                del post['lastpost']
            result['post'] = post
        else:
            result['status'] = 'no post found'
        self.write(json.dumps(result))


# move thread to different board
class AjaxMoveHandler(LoggedInHandler):

    @ifadmin
    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        data = data['post'].decode('utf-8').split('-')
        destination = data[0]
        pid = int(data[-1])
        response = {}
        thread = await db.posts.find_one({'count': pid})
        if thread:
            posts = await db.posts.find({'thread': thread['count']}).to_list(None)
            for post in posts:
                post['board'] = destination
                await update_db(db, post['count'], post)
            log_message = 'Thread #{0} has been moved from board /{1}/ to board /{2}/'.format(
                thread['count'],
                thread['board'],
                destination
            )
            await log('other', log_message)
            thread['board'] = destination
            await update_db(db, thread['count'], thread)
            response['status'] = ['Moved']
        else:
            response = {'status': 'Error moving thread.'}
        self.write(json.dumps(response))


# gets information used to fill in map with data
class AjaxMapHandler(tornado.web.RequestHandler):

    async def post(self):
        db = self.application.database
        posters = await db.maps.find({}).to_list(None)
        for poster in posters:
            del poster['_id']
            poster['date'] = poster['date'].strftime("%Y-%m-%d %H:%M:%S")
        self.write(json.dumps(posters))

# poorchanga seal of approval
class AjaxSealHandler(tornado.web.RequestHandler):

    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        pid = int(data['post'].decode('utf-8'))
        post = await db.posts.find_one({'count': pid})
        post['seal'] = True
        await update_db(db, post['count'], post)
        self.write(json.dumps({'status': 'success'}))