import datetime
import json
import logging

import motor.motor_tornado
import tornado.web

from src.logger import log
from src.utils import (
    exclude,
)
from src.userhandle import User, AUTH_METHODS

board_exclude_fields = ['_id', 'created', ]
post_exclude_fields = ['_id', 'ip', 'pass', ]

AUTH_HEADER = 'Authorization'


class APIHandler(tornado.web.RequestHandler):
    def initialize(self, *args, **kwargs):
        self.logger = logging.getLogger("API")
        self.con = motor.motor_tornado.MotorClient("localhost", 27017)
        self.database = self.con["imageboard"]
        self.__user = None
        self.users = self.database.users
        self.__boards = None
        self.logger.info("finished initialization")
        self.headers = self.request.headers
        print(self.current_user.uid, self.current_user.user, self.current_user.is_admin)

    def get_or_create_user(self) -> User:
        api_key = self.headers.get(AUTH_HEADER)
        self.__user = User(uid=api_key, using=AUTH_METHODS.APIKEY)
        return self.__user

    def reset_user(self):
        self.__user = None
        self.clear_header(AUTH_HEADER)

    def get_current_user(self) -> User:
        return self.get_or_create_user()

    @property
    def user(self) -> User:
        return self.get_or_create_user()

    def check_origin(self, origin) -> bool:  # type: ignore
        return True

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')

    def options(self):
        self.set_status(204)
        self.finish()

    @property
    async def boards(self) -> list[dict]:
        if not self.__boards:
            self.__boards = await self.database.boards.find({}, {"_id": False}).to_list(
                None
            )
        return self.__boards

    @property
    async def moderated_boards(self) -> list[dict]:
        if self.user.is_admin_or_moderator:
            if not self.user.is_admin:
                return list(filter(
                    lambda board: board.get('short') in self.user.moderated_boards,
                    await self.boards
                ))
            return await self.boards

        return []


class GetBoards(APIHandler):
    async def get(self):
        boards = await self.database.boards.find({}, exclude(board_exclude_fields)).to_list(None)
        self.write(json.dumps(boards))


class GetThreads(APIHandler):
    async def get(self, board: str):
        db_board = await self.database.bboards.find_one({'short': board}, exclude(board_exclude_fields))
        if db_board:
            threads = await self.database.posts.find(
                    {
                        'board': board,
                        'oppost': True,
                    }, exclude(post_exclude_fields)
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


class GetPosts(APIHandler):
    async def get(self, board: str, thread: int):
        thread = int(thread)
        op = await self.database.posts.find_one({'count': thread}, exclude(post_exclude_fields))
        if op:
            op['date'] = op['date'].strftime("%Y-%m-%d %H:%M:%S")
            op['lastpost'] = op['lastpost'].strftime("%Y-%m-%d %H:%M:%S")
            res = [op, ]
            posts = await self.database.posts.find(
                {'thread': thread}, exclude(post_exclude_fields)
            ).sort([('count', 1)]).to_list(None)
            for post in posts:
                post['date'] = post['date'].strftime("%Y-%m-%d %H:%M:%S")
                post = {k: v for k, v in post.items() if v}
                res.append(post)
            self.write(json.dumps(res, indent=4, ensure_ascii=False))
        else:
            self.set_status(404)
            self.write({'status': 'Thread not found'})
