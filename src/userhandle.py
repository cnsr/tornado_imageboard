import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from src.utils import generate_password, verify_password

import motor.motor_tornado
import pymongo
import tornado.web

logger = logging.getLogger("board")

ANONIMOUS_USER = "anon"
REGISTERED_USER = "registered"
ADMIN_USER = "admin"

POSSIBLE_USER_TYPES = [
    ANONIMOUS_USER,
    REGISTERED_USER,
    ADMIN_USER,
]


def create_admin_user(self, password):
    User("1", ADMIN_USER, password)


# TODO: refactor in case this works at all
class User:
    def __init__(
        self,
        uid: Optional[str],
        role: Optional[str] = ANONIMOUS_USER,
        password: Optional[str] = None,
    ):
        # set default variables
        self.connection = pymongo.MongoClient("localhost", 27017).imageboard
        self.db = self.connection.users
        self.__created_at = None
        self.__type = role
        self.__user = None
        self.__username = None

        # get or create user
        if uid:
            self.uid = uid
        else:
            self.uid = uuid4().hex
            self.create_user(role)
            if password:
                self.set_password(password)

    def create_user(
        self,
        user_type: Optional[str] = ANONIMOUS_USER,
        username: Optional[str] = "Unknown",
    ):
        # created_at is a UTC timestamp
        self.__user = self.db.insert_one(
            {
                "id": self.uid,
                "created_at": self.created_at,
                "type": user_type,
                "moderated_boards": [],
                "username": username,
            }
        )
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
        return datetime.fromtimestamp(self.__created_at).strftime("%m/%d/%Y, %H:%M:%S")

    @property
    def moderated_boards(self):
        # TODO: lookup actual boards
        return self.user.get('moderated_boards', [])

    def set_password(self, raw_password: str):
        self.db.update_one(
            {"id": self.uid},
            {
                "$set": {"password": generate_password(raw_password)},
            },
            upsert=False,
        )

    def verify_password(self, password: str) -> bool:
        hashed_password = self.retrieve_user(include_password=True).get("password")
        return verify_password(password, hashed_password)

    def retrieve_user(self, include_password: bool = False) -> dict[str, str]:
        user = self.db.find_one(
            {"id": self.uid}, {"_id": False, "password": include_password}
        )
        self.__created_at = user.get("created_at")
        self.__type = user.get("type")
        self.__user = user
        self.__username = (
            user.get("username") if user.get("username") != "Unknown" else None
        )
        return user

    def __update(self, data: dict[str, str]):
        # prevent overriding of default fields
        for forbidden_field in ["uid", "created_at"]:
            if data.get(forbidden_field):
                data.pop(forbidden_field)

        self.db.find_one_and_update(
            {"id": self.uid}, {"$set": data}, {"_id": False}, upsert=False
        )

    def login(self, username: str, password: str) -> Optional["User"]:  # type: ignore
        cached_user = self.db.find_one({"username": username}, {"_id": False})
        print(cached_user, password)
        if cached_user and verify_password(password, cached_user.get("password")):
            self.uid = cached_user.get("id")
            self.__created_at = cached_user.get("created_at")
            self.__type = cached_user.get("type")
            self.__user = cached_user
            return self

    def register(self, username: str, password: str):
        self.__update({"username": username})
        self.set_password(password)

    @property
    def user(self):
        if not self.__user:
            self.retrieve_user()
        return self.__user

    @property
    def is_admin(self) -> bool:
        return self.__type == ADMIN_USER

    @property
    def is_logged_in(self) -> bool:
        return self.__username is not None and self.__username != "Unknown"


class UserHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.logger = logger
        self.con = motor.motor_tornado.MotorClient("localhost", 27017)
        self.database = self.con["imageboard"]
        self.users = self.database.users
        self.__boards = None
        logger.info("finished initialization")
        print(self.current_user.uid, self.current_user.user)

    def get_or_create_user(self) -> User:
        user_id = self.get_cookie("ib-user", None)
        self.user = User(user_id)
        if self.user.uid != user_id:
            self.set_cookie("ib-user", self.user.uid)
        return self.user

    def get_current_user(self) -> User:
        return self.get_or_create_user()

    def authenticate(self, username: str, password: str) -> bool:
        if authenticated_user := self.user.login(username, password):
            print("auth user", authenticated_user)
            if authenticated_user:
                self.user = authenticated_user
                self.set_cookie("ib-user", self.user.uid)
                return True
        return False

    def check_origin(self, origin):
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


class ProfilePage(UserHandler):
    async def get(self):
        raw_errors = {
            "notimplemented": "Functionality not yet implemented",
            "fail": "Failed to authenticate",
        }

        errors = [
            raw_errors.get(err, "Unknown error")
            for err in self.get_query_arguments("error")
        ]

        self.render("profile.html", boards=await self.boards, errors=errors)

    async def post(self):
        action = self.get_argument("action")
        username = self.get_argument("username")
        password = self.get_argument("password")

        target = "/profile"

        if action == "login":
            success = self.authenticate(username, password)
            if not success:
                target = f"{target}?error=fail"
        elif action == "register":
            self.user.register(username, password)
            success = self.authenticate(username, password)
            if not success:
                target = f"{target}?error=fail"
        else:
            target = f"{target}?error=notimplemented"

        self.redirect(target)
