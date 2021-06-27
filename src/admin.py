import datetime
import re
from uuid import uuid4

import motor.motor_tornado
import tornado.web

import src.ib_settings as _ib
from src.logger import log
from src.utils import (
    ifadmin, admin_or_mod_required, admin_required,
    remove_files, update_db, get_ip,
    save_blacklist, get_blacklist,
)
from src.models import Board

from src.userhandle import UserHandler


class AdminLoginHandler(UserHandler):

    async def get(self):
        if not self.current_user:
            await self.render('admin/admin_login.html', boards=await self.boards)
        else:
            self.redirect('/profile')

    async def post(self):
        password = self.get_argument('password')
        ip = await get_ip(self.request)
        is_authenticated = self.user.authenticate(self.user.username, password)
        if self.user.is_admin and is_authenticated:
            log_message = f'{ip} has logged in as admin'
            await log('other', log_message)
            self.redirect('/admin')
        elif self.user.is_admin_or_moderator:
            log_message = f'{ip} has logged in as moderator'
            await log('other', log_message)
            self.redirect('/admin')
        else:
            log_message = f'{ip} has attempted to log in as admin'
            await log('other', log_message)
            self.redirect('/profile')


class AdminLogoutHandler(UserHandler):
    @admin_or_mod_required
    async def get(self):
        self.clear_cookie('adminlogin')
        ip = await get_ip(self.request)
        log_message = f'{ip} has logged in as admin'
        await log('other', log_message)
        self.redirect('/')


# stats of boards for admins
class AdminStatsHandler(UserHandler):
    responses = {
        'success': 'Deletion successful.',
        'error': 'Board does not exist.'
    }

    @admin_or_mod_required
    async def get(self):
        popup = None
        if self.get_arguments('msg'):
            msg = self.get_argument('msg')
            popup = self.responses.get(msg)

        await self.render('admin/admin_stats.html', boards=await self.moderated_boards, popup=popup)

    @ifadmin
    async def post(self):
        short = self.get_argument('short')
        board = await self.database.boards.find_one({'short': short})
        url = self.request.uri.split('?')[0]
        if board:
            try:
                posts = await self.database.posts.find({'board': board['short']}).to_list(None)
                for post in posts:
                    await remove_files(post)
                    await self.database.posts.delete_one({'count': post['count']})
                log_message = 'Board {0} has been deleted.'.format(board['short'])
                await log('board_remove', log_message)
                await self.database.boards.delete_one({'short':short})
                self.redirect(url + '?msg=success')
            except Exception as e:
                print(f"Exception when trying to POST stats page {e}, u: {self.user}")
                self.redirect(url + '?msg=error1')
        else:
            self.redirect(url + '?msg=error')


# you can view bans here
class AdminBannedHandler(UserHandler):
    # only absolute admins can view bans
    @admin_required
    async def get(self):
        bans = await self.database.bans.find({}).sort([('date', 1)]).to_list(None)
        await self.render('admin/admin_banned.html', bans=bans, boards=await self.boards)

    @admin_required
    async def post(self):
        ip = self.get_argument('ip')
        await self.database.bans.delete_one({'ip': ip})
        log_message = '{0} was unbanned by admin.'.format(ip)
        await log('unban', log_message)
        self.redirect('/admin/bans')


# you can view reports here
class AdminReportsHandler(UserHandler):
    @admin_or_mod_required
    async def get(self):
        reports = await self.database.reports.find({}).sort([('date', 1)]).to_list(None)
        await self.render('admin/admin_reported.html', reports=reports, boards=await self.moderated_boards)

    @admin_or_mod_required
    async def post(self):
        ip = self.get_argument('ip')
        if ip != 'all':
            await self.database.reports.delete_one({'ip': ip})
        else:
            await self.database.reports.remove({})
        self.redirect('/admin/reports')


# admin main page
class AdminHandler(UserHandler):

    @admin_or_mod_required
    async def get(self):
        await self.render('admin/admin.html', boards=await self.moderated_boards)


# creation of boards
class AdminBoardCreationHandler(UserHandler):
    @admin_or_mod_required
    async def get(self):
        await self.render('admin/admincreate.html', boards=await self.moderated_boards)

    @admin_or_mod_required
    async def post(self):
        # TODO: take care of moderators
        # TODO: add proper server-side validation
        data = dict()
        data['name'] = self.get_argument('name', '')
        data['short'] = self.get_argument('short', '')
        data['username'] = self.get_argument('username', '')
        data['description'] = self.get_argument('description', '')
        data['thread_posts'] = int(self.get_argument('thread_posts', '15'))
        data['thread_bump'] = int(self.get_argument('thread_bump', '10'))
        data['thread_catalog'] = int(self.get_argument('thread_catalog', '10'))
        data['country'] = 'country' in self.request.arguments
        data['custom'] = 'custom' in self.request.arguments
        data['roll'] = 'roll' in self.request.arguments
        data['unlisted'] = 'unlisted' in self.request.arguments
        # data['postcount'] = 0
        # data['mediacount'] = 0
        # data['created'] = datetime.datetime.utcnow()
        # data['banners'] = []
        data['perpage'] = int(float(self.get_argument('perpage', '10')))
        data['pinned'] = None
        board = Board.from_dict(data)
        print('created board:', board)
        print('board as dict:', dict(board))
        if self.request.files:
            f = self.request.files['banner'][0]
            ext = f['filename'].split('.')[-1]
            new_name = f"banners/{data.get('short')}-{uuid4().hex[:8]}.{ext}"
            with open(new_name, 'wb') as nf:
                nf.write(bytes(f['body']))
            board.add_banner(new_name)
        log_message = f'Board /{board.short}/ has been created.'
        await log('board_creation', log_message)
        await self.database.boards.insert_one(dict(board))
        self.redirect('/' + data['short'])


# editing existing boards
class AdminBoardEditHandler(UserHandler):
    @admin_or_mod_required
    async def get(self, board):
        instance = await self.database.boards.find_one({'short': board})
        to_remove = ['postcount', 'mediacount', 'created']
        if instance:
            for key in to_remove:
                if key in instance:
                    del instance[key]
            await self.render(
                'admin/admin_edit.html', boards=await self.moderated_boards, i=instance
            )
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
class AdminLogsHandler(UserHandler):
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
        self.render('admin/admin_logs.html', logs=logs, boards=await self.boards, paged=paged, current=current,
        log_types=log_types, curr_type=log_type)

    async def chunkify(self, l, n=30):
        res = list()
        for i in range(0, len(l), n):
            res.append(l[i:i + n])
        return res


class AdminBlackListHandler(UserHandler):
    @ifadmin
    async def get(self):
        db = self.application.database
        blacklist = get_blacklist()
        self.render('admin/admin_blacklist.html', boards=await self.boards, blacklist=blacklist)

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


class AdminIPSearchHandler(UserHandler):
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
        post = await self.application.database.posts.find_one({'count': int(count)}) or None
        banned = await self.application.database.bans.find_one({'ip': post['ip']}) or None
        if post:
            posts_by_same_ip = await self.application.database.posts.find({'ip': post['ip']}).sort('date', -1).to_list(None)
            self.render('admin/admin_search.html',
                        boards=await self.boards, popup=popup,
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
