import tornado.web
import json
import datetime
import motor.motor_tornado

from utils import *

# delete posts using ajax; doesnt have admin rights check and idk how to make it
class AjaxDeleteHandler(tornado.web.RequestHandler):

    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        pid = int(data['post'].decode('utf-8'))
        post = await db.posts.find_one({'count': pid})
        response = {'succ':'ess'}
        if post['oppost']:
            posts = await db.posts.find({'thread': post['count']}).to_list(None)
            for post in posts:
                await removeing(post)
                await db.posts.delete_one({'count': post['count']})
            response['op'] = 'true'
        await removeing(post)
        await db.posts.delete_one({'count': pid})
        self.write(json.dumps(response))


# reporting users using ajax; same stuff as with previous one
class AjaxReportHandler(tornado.web.RequestHandler):

    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        p = await db.posts.find_one({'count': int(data['post'])})
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
        await db.reports.insert(report)
        response = {'ok': 'ok'}
        self.write(json.dumps(response))


class AjaxInfoHandler(tornado.web.RequestHandler):

    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        for k, v in data.items(): data[k] = v.decode('utf-8')
        p = await db.posts.find_one({'count': int(data['post'])})
        del p['_id']
        p['date'] = p['date'].strftime("%Y-%m-%d %H:%M:%S")
        if p.get('lastpost', ''):
            p['lastpost'] = p['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
        self.write(json.dumps(p, indent=4, ensure_ascii=False))


class AjaxPinHandler(tornado.web.RequestHandler):

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


class AjaxLockHandler(tornado.web.RequestHandler):

    async def post(self):
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


# banner deleting handler
class AjaxBannerDelHandler(tornado.web.RequestHandler):

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


# banning users using ajax; same stuff as with previous one
class AjaxBanHandler(tornado.web.RequestHandler):

    async def post(self):
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
            await db.bans.insert(ban)
            p['banned'] = True
            if ban['locked'] and p['oppost']:
                p['locked'] = True
            await update_db(db, p['count'], p)
        response = {'ok': 'ok'}
        self.write(json.dumps(response))


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
class AjaxDeletePassHandler(tornado.web.RequestHandler):

    async def post(self):
        db = self.application.database
        data = dict((k,v[-1] ) for k, v in self.request.arguments.items())
        pid = int(data['post'].decode('utf-8'))
        password = data['password'].decode('utf-8')
        post = await db.posts.find_one({'count': pid})
        if post['pass'] == password:
            if post['oppost']:
                posts = await db.posts.find({'thread': post['count']}).to_list(None)
                for post in posts:
                    await removeing(post)
                    await db.posts.delete_one({'count': post['count']})
                response = {'status':'deleted'}
                response['op'] = 'true'
            await removeing(post)
            await db.posts.delete_one({'count': pid})
            self.write(json.dumps(response))
        else:
            self.write(json.dumps({'status': 'passwords do not match'}))


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
            result['post'] = post
        else:
            result['status'] = 'no post found'
        self.write(json.dumps(result))

