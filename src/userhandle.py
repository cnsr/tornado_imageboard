import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, Any
from uuid import uuid4
from enum import Enum
from src.utils import generate_password, verify_password
import jwt

import motor.motor_tornado
import pymongo
import tornado.web

logger = logging.getLogger("board")
load_dotenv()

ANONIMOUS_USER = "anon"
REGISTERED_USER = "registered"
ADMIN_USER = "admin"
MODERATOR_USER = "moderator"

POSSIBLE_USER_TYPES = [
    ANONIMOUS_USER,
    REGISTERED_USER,
    ADMIN_USER,
    MODERATOR_USER,
]


# TODO: remove this comment


USER_AS_DICT = dict[str, Union[str, int, list[str]]]


class AUTH_METHODS(Enum):
    COOKIE = 'cookie'
    APIKEY = 'api_key'


def create_admin_user(password: Optional[str] = None):
    if not password:
        password = os.getenv('ADMIN_PASSWORD')
    try:
        u = User("1", ADMIN_USER, password)
        u.set_username("admin")
        print(u.__dict__)
    except AssertionError:
        print("User with such username (admin) already exists")


# TODO: refactor in case this works at all
# TODO: hash and store user IPs (hash against a .env salt)
# TODO: allow generation of API tokens for admins/mods and use a cookie auth method
class User:
    def __init__(
        self,
        uid: Optional[str],
        role: Optional[str] = ANONIMOUS_USER,
        password: Optional[str] = None,
        using: AUTH_METHODS = AUTH_METHODS.COOKIE,
    ):
        # set default variables
        self.connection = pymongo.MongoClient("localhost", 27017).imageboard
        self.db = self.connection.users
        self.__created_at = None
        self.__type = role
        self.__user: USER_AS_DICT = {}
        self.__username = None
        self.auth_method = using

        # FIXME: a new user is being created for a fresh session

        if self.auth_method is AUTH_METHODS.COOKIE:
            # get or create user
            if uid:
                self.uid = uid
            else:
                self.uid = uuid4().hex
            if not self.__user:
                self.create_user(role)
            if password:
                self.set_password(password)
        elif self.auth_method is AUTH_METHODS.APIKEY:
            # TODO: auth using api key - find a user with the key first tho
            pass

    def create_user(
        self,
        user_type: Optional[str] = ANONIMOUS_USER,
        username: Optional[str] = "Unknown",
    ):
        # created_at is a UTC timestamp
        if user_type == ADMIN_USER and username == "Unknown":
            username = "admin"

        if username != "Unknown":
            if self.uid:
                existing_user = self.db.find_one({"id": str(self.uid)})
            else:
                existing_user = self.db.find_one({"username": username})
            if existing_user:
                raise Exception("Tried to create already existing user")
        result = self.db.insert_one(
            {
                "id": str(self.uid),
                "created_at": self.created_at,
                "type": user_type,
                "moderated_boards": [],
                "username": username,
            }
        )
        if not result.inserted_id:
            raise Exception("Failed to write user to db")
        self.retrieve_user()
        self.__username = username if username != "Unknown" else None  # type: ignore

    @property
    def user_type(self):
        if not self.__type or self.__type not in POSSIBLE_USER_TYPES:
            return ANONIMOUS_USER
        return self.__type

    @property
    def username(self):
        return self.__username or 'Unknown'

    @property
    def created_at(self):
        if not self.__created_at:
            return datetime.now().replace(tzinfo=timezone.utc).timestamp()
        return self.__created_at

    @property
    def pretty_created_at(self):
        return datetime.fromtimestamp(self.created_at).strftime("%m/%d/%Y, %H:%M:%S")

    @property
    def moderated_boards(self) -> list[str]:
        # TODO: lookup actual boards
        return self.user.get('moderated_boards', [])  # type: ignore

    def set_password(self, raw_password: str):
        self.db.find_one_and_update(
            {"id": str(self.uid)},
            {
                "$set": {"password": generate_password(raw_password)},
            },
            upsert=False,
        )

    def verify_password(self, password: str) -> bool:
        if hashed_password := self.retrieve_user_password():
            return verify_password(password, hashed_password)
        return False

    def verify_api_key(self, api_key: str) -> bool:
        return api_key in self.api_keys

    @property
    def api_keys(self) -> list[str]:
        result = self.db.find_one(
            {"id": str(self.uid)}, {"_id": False, "password": False}
        )
        if result:
            return result.get('api_keys', [])
        return []

    def generate_api_key(self):
        max_api_keys = int(os.getenv("MAX_API_KEYS", "3"))
        current_keys = self.api_keys
        if len(current_keys) < max_api_keys and not self.is_admin:
            raise Exception("API keys quota exceeded")
        else:
            new_api_key = jwt.encode({
                    'userId': self.uid,
                    'issuedAt': str(datetime.now()),
                },
                os.getenv('JWT_SECRET', 'secret'), algorithm="HS256",
            ).decode('utf-8')
            current_keys.append(new_api_key)

    def validate_api_key(self, api_key: str) -> bool:
        payload: dict[str, Any] = jwt.decode(api_key, os.getenv('JWT_SECRET', 'secret'), algorithm='HS256')
        # if the issuedAt is missing, key is handled as if it is expired
        if not payload.get('issuedAt') or not payload.get('userId'):
            raise Exception("Token payload is invalid")
        issuedAt = datetime.strptime(payload.get("issuedAt"), "%Y-%m-%d %H:%M:%S.%f")  # type: ignore
        if issuedAt < (datetime.now() + timedelta(days=365)):
            raise Exception("The API key has expired. Please, issue a new one")
        return payload.get("userId", "1") == self.uid

    def retrieve_user_password(self) -> str:
        result = self.db.find_one(
            {"id": str(self.uid)}, {"_id": False, "password": True}
        )
        if result:
            return result.get("password", "")
        return ""

    def retrieve_user(self):
        stored_user = self.db.find_one(
            {"id": str(self.uid)}, {"_id": False, "password": False}
        )
        if stored_user:
            self.__created_at = stored_user.get("created_at")
            self.__type = stored_user.get("type")
            self.__user = stored_user
            self.__username = (
                stored_user.get("username") if stored_user.get("username") != "Unknown" else None
            )
            print(self.__username)
        else:
            self.create_user()

    def __update(self, data: dict[str, str]):
        # prevent overriding of default fields
        for forbidden_field in ["uid", "created_at"]:
            if data.get(forbidden_field):
                data.pop(forbidden_field)

        self.db.find_one_and_update(
            {"id": str(self.uid)}, {"$set": data}, {"_id": False}, upsert=False
        )

    def set_username(self, username: str):
        self.db.find_one_and_update(
            {"id": str(self.uid)}, {"$set": {"username": username}}, {"_id": False}, upsert=False
        )

    def login(self, username: str, password: str) -> Optional["User"]:  # type: ignore
        cached_user = self.db.find_one({"username": username}, {"_id": False})
        print(f'Found cached user: {cached_user}did')
        print(f"Result of password validation: {verify_password(password, cached_user.get('password'))}")
        if cached_user and verify_password(password, cached_user.get("password")):
            print('setting cached user as current user')
            self.uid = cached_user.get("id")
            self.__created_at = cached_user.get("created_at")
            self.__type = cached_user.get("type")
            self.__user = cached_user
            return self

    def register(self, username: str, password: str):
        forbidden_usernames = [
            'admin', 'moderator', 'staff', 'administrator', 'administration'
        ]
        if username in forbidden_usernames:
            return
        self.register_unsafe(username, password)

    def register_unsafe(self, username: str, password: str):
        self.__update({"username": username})
        self.set_password(password)
        self.login(username, password)

    @property
    def user(self) -> USER_AS_DICT:
        if not self.__user:
            self.retrieve_user()
        return self.__user

    @property
    def is_admin(self) -> bool:
        return self.__type == ADMIN_USER

    @property
    def is_admin_or_moderator(self) -> bool:
        return self.__type in (ADMIN_USER, MODERATOR_USER)

    def moderates_board(self, board: str) -> bool:
        return self.is_admin or board in self.moderated_boards

    @property
    def is_logged_in(self) -> bool:
        # users have shitty username thus this shit was introduced
        if self.__type == ADMIN_USER:
            return True
        return self.__username is not None and self.__username != "Unknown"


# noinspection PyAttributeOutsideInit
class UserHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.logger = logging.getLogger("board")
        self.con = motor.motor_tornado.MotorClient("localhost", 27017)
        self.database = self.con["imageboard"]
        self.__user = None
        self.users = self.database.users
        self.__boards = None
        logger.info("finished initialization")
        print(self.current_user.uid, self.current_user.user, self.current_user.is_admin)

    def get_or_create_user(self) -> User:
        user_id = self.get_cookie("ib-user", None)
        self.__user = User(user_id, using=AUTH_METHODS.COOKIE)
        if self.__user.uid != user_id:
            self.set_cookie("ib-user", self.__user.uid)
        return self.__user

    def reset_user(self):
        self.__user = None
        self.clear_cookie('ib-user')
        self.clear_cookie('adminlogin')

    def get_current_user(self) -> User:
        return self.get_or_create_user()

    @property
    def user(self) -> User:
        return self.get_or_create_user()

    def authenticate(self, username: str, password: str) -> bool:
        if authenticated_user := self.user.login(username, password):
            print('did authenticate just there just now', authenticated_user)
            self.__user = authenticated_user
            self.current_user = authenticated_user
            self.set_cookie("ib-user", self.__user.uid)
            # this shit literally resets the user ?
            # self.set_cookie("ib-user", self.user.uid)
            return True
        return False

    def check_origin(self, origin) -> bool:  # type: ignore
        return True

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, PUT, OPTIONS')

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

    async def get_latest_postnumber(self) -> int:
        try:
            #latest_post = await self.database.posts.find({}).sort([('count', -1), ]).to_list(None)
            #return latest_post[0]['count']
            latest_post = await self.database.posts.find(sort=[("count", -1),])
            return latest_post.get('count', 0)
        except IndexError:
            # in case you are running the server for the first time
            # there will be no posts therefore this should return 0
            # and the first post will be №1
            return 0


class ProfilePage(UserHandler):
    async def get(self):
        raw_errors = {
            "notimplemented": "Functionality not yet implemented",
            "fail": "Failed to authenticate",
            "miss": "Missing either the username or the password",
        }

        errors = [
            raw_errors.get(err, "Unknown error")
            for err in self.get_query_arguments("error")
        ]

        await self.render("profile.html", boards=await self.boards, errors=errors)

    async def post(self):
        action = self.get_argument("action")
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        print(f'PARAMS: {action} | {username} | {password}')
        target = "/profile"

        if action in ['login', 'register']:
            if not username or not password:
                self.redirect(f"{target}?error=miss")
            if action == "register":
                self.user.register(username, password)
            success = self.authenticate(username, password)
            if not success:
                target = f"{target}?error=fail"
        elif action == 'logout':
            if self.user and self.user.is_logged_in:
                self.reset_user()
        else:
            target = f"{target}?error=notimplemented"

        self.redirect(target)
