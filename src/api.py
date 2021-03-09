import datetime
import json

import motor.motor_tornado
import tornado.web

from src.logger import log
from src.utils import *

board_exclude_fields = ['_id', 'created',]
post_exclude_fields = ['_id', 'ip', 'pass']

class GetBoards(tornado.web.RequestHandler):
    async def get(self):
        db = self.application.database
        boards = await db.boards.find({}, exclude(board_exclude_fields)).to_list(None)
        self.write(json.dumps(boards))


class GetThreads(tornado.web.RequestHandler):
    async def get(self, board: str):
        db = self.application.database
        db_board = await db.boards.find_one({'short': board}, exclude(board_exclude_fields))
        if db_board:
            threads = await db.posts.find(
                    {'board': board,'oppost': True}, exclude(post_exclude_fields)
                ).sort([('pinned', -1), ('lastpost', -1)]).to_list(None)
            if threads:
                for thread in threads:
                    thread['date'] = thread['date'].strftime("%Y-%m-%d %H:%M:%S")
                    thread['lastpost'] = thread['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
                self.write(json.dumps(threads, indent=4, ensure_ascii=False))
            else:
                self.set_status(404)
                self.write({'status': 'Threads not found'})
        else:
            self.set_status(404)
            self.write({'status': 'Board not found'})


class GetPosts(tornado.web.RequestHandler):
    async def get(self, board: str, thread: int):
        db = self.application.database
        thread = int(thread)
        op = await db.posts.find_one({'count': thread}, exclude(post_exclude_fields))
        if op:
            op['date'] = op['date'].strftime("%Y-%m-%d %H:%M:%S")
            op['lastpost'] = op['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
            res = [op]            
            posts = await db.posts.find({'thread': thread}, exclude(post_exclude_fields)).sort([('count', 1)]).to_list(None)
            for post in posts:
                post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
                post = {k:v for k,v in post.items() if v != None}
                res.append(post)
            self.write(json.dumps(res, indent=4, ensure_ascii=False))
        else:
            self.set_status(404)
            self.write({'status': 'Thread not found'})
