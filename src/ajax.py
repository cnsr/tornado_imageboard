import datetime

from functools import cached_property

from src.logger import log
from src.utils import *
from src.userhandle import UserHandler


class BaseAjaxHandler(UserHandler):
    @cached_property
    def post_data(self) -> dict[str, str]:
        return dict((k, v[-1].decode('utf-8')) for k, v in self.request.arguments.items())


# delete posts using ajax
class AjaxDeleteHandler(BaseAjaxHandler):

    # TODO: allow mods delete their own threads
    @admin_required
    async def post(self):
        pid = int(self.post_data['post'])
        post = await self.database.posts.find_one({'count': pid})
        if post:
            replies_to = await self.database.posts.find({'replies': {'$in': [pid]}}).to_list(None)
            for reply in replies_to:
                reply['replies'].remove(pid)
                await update_db(self.database, reply['count'], reply)
            response = {}
            if post['oppost']:
                posts = await self.database.posts.find({'thread': post['count']}).to_list(None)
                for post in posts:
                    await remove_files(post)
                    await self.database.posts.delete_one({'count': post['count']})
                response['op'] = 'true'
            await remove_files(post)
            if post['oppost']:
                log_message = 'Thread #{0} has been removed by admin'.format(pid)
            else:
                log_message = 'Post #{0} has been removed by admin'.format(pid)
            await log('post_remove', log_message)
            await self.database.posts.delete_one({'count': pid})
            response['status'] = ['deleted']
        else:
            response = {'status': 'Error deleting post.'}
        self.write(json.dumps(response))


# reporting users using ajax, doesnt need admin check
class AjaxReportHandler(BaseAjaxHandler):

    async def post(self):
        p = await self.database.posts.find_one({'count': int(self.post_data['post'])}, {'_id': False})
        report = {
            'ip': p['ip'],
            'post': int(self.post_data['post']),
            'reason': self.post_data['reason'],
            'date': datetime.datetime.utcnow(),
        }
        if not p['oppost']:
            report['url'] = '/' + p['board'] + '/thread/' + str(p['thread']) + '#' + str(p['count'])
        else:
            report['url'] = '/' + p['board'] + '/thread/' + str(p['count']) + '#' + str(p['count'])
        log_message = 'Report has been sent for post #{0} with ip {1}.'.format(p['count'], p['ip'])
        await log('post_remove', log_message)
        await self.database.reports.insert_one(report)
        response = {'ok': 'ok'}
        self.write(json.dumps(response))


# gives info about post
class AjaxInfoHandler(BaseAjaxHandler):

    @ifadmin
    async def post(self):
        p = await self.database.posts.find_one({'count': int(self.post_data['post'])}, {'_id': False})
        if p:
            p['date'] = p['date'].strftime("%Y-%m-%d %H:%M:%S")
            if p.get('lastpost', ''):
                p['lastpost'] = p['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
            self.write(json.dumps(p, indent=4, ensure_ascii=False))
        else:
            self.write(json.dumps({'error': 'post does not exist. perhaps, it has been deleted?'}))


# pins threads
class AjaxThreadPinHandler(BaseAjaxHandler):

    @ifadmin
    async def post(self):
        pst = self.post_data['post']
        # heard that eval is weak shit
        for b in eval(self.post_data['boards']):
            brd = await self.database.boards.find_one({'short': b})
            brd['pinned'] = pst
            await update_db_b(self.database, b, brd)
        self.write(json.dumps({'status': 'ok'}))


# pins the threads so they appear first in query
class AjaxPinHandler(BaseAjaxHandler):

    @ifadmin
    async def post(self):
        thread = await self.database.posts.find_one({'count': int(self.post_data['post'])})
        if thread['oppost']:
            thread['pinned'] = not thread['pinned']
            await update_db(self.database, thread['count'], thread)
            self.write(json.dumps({'status': 'ok'}))
        else:
            self.write(json.dumps({'status': 'failed'}))


# threads are infinite:
# first in - first out,
# posts get deleted when they go beyond thread post limit
class AjaxInfinifyHandler(BaseAjaxHandler):

    @ifadmin
    async def post(self):
        thread = await self.database.posts.find_one({'count': int(self.post_data['post'])})
        if thread['oppost']:
            thread['infinite'] = not thread['infinite']
            await update_db(self.database, thread['count'], thread)
            self.write(json.dumps({'status': 'ok'}))
        else:
            self.write(json.dumps({'status': 'failed'}))


# locks the threads so that they can't be posted in
class AjaxLockHandler(BaseAjaxHandler):

    @ifadmin
    async def post(self):
        thread = await self.database.posts.find_one({'count': int(self.post_data['post'])})
        if thread['oppost']:
            thread['locked'] = not thread['locked']
            await update_db(self.database, thread['count'], thread)
            self.write(json.dumps({'status': 'ok'}))
        else:
            self.write(json.dumps({'status': 'failed'}))


# deletion of banners
class AjaxBannerDelHandler(BaseAjaxHandler):

    @ifadmin
    async def post(self):
        data = dict((k, v[-1].decode('utf-8')) for k, v in self.request.arguments.items())
        brd = await self.database.boards.find_one({'short': data['brd']})
        banner = data['banner']
        if banner in brd['banners']:
            brd['banners'].remove(banner)
            await update_db_b(self.database, brd['short'], brd)
            os.remove(banner)
            self.write(json.dumps({'status': 'ok'}))
        else:
            self.write(json.dumps({'status': 'failed'}))


# banning users
class AjaxBanHandler(BaseAjaxHandler):

    @ifadmin
    async def post(self):
        response = {'ok': 'Banned'}
        p = await self.database.posts.find_one({'count': int(self.post_data['post'])})
        banned = await self.database.bans.find_one({'ip': p['ip']})
        if not banned:
            ban = {
                'ip': p['ip'],
                'ban_post': int(self.post_data['post']),
                'reason': self.post_data['reason'],
                'locked': False,
                'date': None,
                'date_of': datetime.datetime.utcnow(),
            }
            if self.post_data['lock'] == 'true':
                ban['locked'] = True
            if self.post_data['date'] != 'Never':
                ban['date'] = self.post_data['date']
            if not p['oppost']:
                ban['url'] = '/' + p['board'] + '/thread/' + str(p['thread']) + '#' + str(p['count'])
            else:
                ban['url'] = '/' + p['board'] + '/thread/' + str(p['count']) + '#' + str(p['count'])
            log_message = '{0} was banned for post #{1} (unban {2}).'.format(p['ip'], p['count'], ban['date'])
            await log('unban', log_message)
            await self.database.bans.insert_one(ban)
            p['banned'] = True
            p['ban_message'] = self.post_data.get('ban_message', 'User has been banned for this post')
            if ban['locked'] and p['oppost']:
                p['locked'] = True
            await update_db(self.database, p['count'], p)
            if self.post_data['rm'] == 'true':
                if p['oppost']:
                    posts = await self.database.posts.find({'thread': p['count']}).to_list(None)
                    for subp in posts:
                        await remove_files(subp)
                    await self.database.posts.delete_many({'thread': p['count']})
                await remove_files(p)
                await self.database.posts.delete_one({'count': p['count']})
        # TODO: make so it only updates the ban info and keep the post deletion/locking unchanged
        else:
            if self.post_data['date'] != 'Never':
                banned['date'] = self.post_data['date']
            else:
                banned['date'] = None
            banned['date_of'] = datetime.datetime.utcnow()
            await self.database.bans.update_one({'ip': banned['ip']}, {"$set": banned}, upsert=False)
            p['banned'] = True
            await update_db(self.database, p['count'], p)
        self.write(json.dumps(response))


# gets posts that have been posted since user loaded the page
class AjaxNewHandler(BaseAjaxHandler):

    async def post(self, board, thread):
        try:
            pid = int(self.post_data['latest'])
            post = await self.database.posts.find_one({'count': pid})
            posts = await self.database.posts.find({'thread': int(thread)}).to_list(None)
            response = []
            for post in posts:
                if int(post['count']) <= pid:
                    del post
                else:
                    del post['_id']
                    del post['ip']
                    post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
                    post['text'] = ''.join(post['text'].split('<br />'))
                    post['isop'] = post.pop('op')
                    response.append(post)
            self.write(json.dumps(response))
        except KeyError:
            posts = await self.database.posts.find({'thread': int(thread)}).to_list(None)
            for post in posts:
                del post['_id']
                del post['ip']
                post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
            self.write(json.dumps(posts))


# delete posts using ajax if password is correct
# therefore, doesn't need admin check
class AjaxDeletePassHandler(BaseAjaxHandler):

    async def post(self):
        pid = int(self.post_data['post'])
        password = self.post_data['password']
        post = await self.database.posts.find_one({'count': pid})
        if post['pass'] == password:
            response = {}
            replies_to = await self.database.posts.find({'replies': {'$in': [pid]}}).to_list(None)
            for reply in replies_to:
                reply['replies'].remove(pid)
                await update_db(self.database, reply['count'], reply)
            if post['oppost']:
                posts = await self.database.posts.find({'thread': post['count']}).to_list(None)
                for post in posts:
                    await remove_files(post)
                    await self.database.posts.delete_one({'count': post['count']})
                response['op'] = 'true'
            await remove_files(post)
            if post['oppost']:
                log_message = 'Thread #{0} has been removed by {1}'.format(pid, post['ip'])
            else:
                log_message = 'Post #{0} has been removed by {1}'.format(pid, post['ip'])
            await log('post_remove', log_message)
            await self.database.posts.delete_one({'count': pid})
            response['status'] = 'deleted'
            self.write(json.dumps(response))
        else:
            self.write(json.dumps({'status': 'passwords do not match'}))


# loads the post from same or different threads on mouseover
class AjaxPostGetter(BaseAjaxHandler):

    async def post(self):
        result = {}
        pid = int(self.post_data['post'])
        post = await self.database.posts.find_one({'count': pid})
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
class AjaxMoveHandler(BaseAjaxHandler):

    @ifadmin
    async def post(self):
        data = self.post_data['post'].split('-')
        destination = data[0]
        pid = int(data[-1])
        response = {}
        thread = await self.database.posts.find_one({'count': pid})
        if thread:
            posts = await self.database.posts.find({'thread': thread['count']}).to_list(None)
            for post in posts:
                post['board'] = destination
                await update_db(self.database, post['count'], post)
            log_message = 'Thread #{0} has been moved from board /{1}/ to board /{2}/'.format(
                thread['count'],
                thread['board'],
                destination
            )
            await log('other', log_message)
            thread['board'] = destination
            await update_db(self.database, thread['count'], thread)
            response['status'] = ['Moved']
        else:
            response = {'status': 'Error moving thread.'}
        self.write(json.dumps(response))


# gets information used to fill in map with data
class AjaxMapHandler(BaseAjaxHandler):

    async def post(self):
        posters = await self.database.maps.find({}).to_list(None)
        for poster in posters:
            del poster['_id']
            poster['date'] = poster['date'].strftime("%Y-%m-%d %H:%M:%S")
        self.write(json.dumps(posters))


# poorchanga seal of approval
class AjaxSealHandler(BaseAjaxHandler):

    async def post(self):
        pid = int(self.post_data['post'])
        post = await self.database.posts.find_one({'count': pid})
        post['seal'] = True
        await update_db(self.database, post['count'], post)
        self.write(json.dumps({'status': 'success'}))
