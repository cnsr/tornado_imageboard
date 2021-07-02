import asyncio
import hashlib
import binascii
import os
import pickle
import re

from enum import Enum
from tornado.httputil import HTTPServerRequest
from typing import Union, Callable

import motor.motor_tornado

PATHLIKE = Union[os.PathLike, str]

MotorDatabase = motor.motor_tornado.MotorDatabase

thumb_def = 'static/missing_thumbnail.jpg'
spoilered = 'static/spoiler.jpg'

VIDEO_EXTENSIONS = ('.webm', '.mp4')
AUDIO_EXTENSION = ('.ogg', '.mp3', '.wav')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.apng', '.bmp')


class FileTypes(Enum):
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'
    UNKNOWN = 'unknown'


def get_filetype(filepath: PATHLIKE) -> FileTypes:
    extension = os.path.splitext(filepath)[-1].lower()
    if extension in VIDEO_EXTENSIONS:
        return FileTypes.VIDEO
    elif extension in AUDIO_EXTENSION:
        return FileTypes.AUDIO
    elif extension in IMAGE_EXTENSIONS:
        return FileTypes.IMAGE
    return FileTypes.UNKNOWN


def generate_password(raw_password: str) -> str:
    # as an alternative, password hash can be stored in .env
    # it doesn't matter as the salt is supposed to be random
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    password_hash = binascii.hexlify(
        hashlib.pbkdf2_hmac('sha512', raw_password.encode('utf-8'), salt, 100000)
    )
    return (salt + password_hash).decode('ascii')


def verify_password(raw_password: str, hashed_password: str) -> bool:
    return hashed_password[64:] == binascii.hexlify(
        hashlib.pbkdf2_hmac('sha512', raw_password.encode('utf-8'), hashed_password[:64].encode('ascii'), 100000)
    ).decode('ascii')


def exclude(_from: list[str]) -> dict:
    return {i: False for i in _from}


# updates one db entry by set parameters
async def update_db(db: MotorDatabase, count: int, variables: dict):
    await db.posts.update_one(
        {'count': count},
        {
            '$set': variables
        },
        upsert=False,
    )


# for updating board data
async def update_db_b(db: MotorDatabase, short: str, variables: dict):
    await db.boards.update_one(
        {'short': short},
        {
            '$set': variables
        },
        upsert=False,
    )


async def check_map(db: MotorDatabase, map_data: dict[str, str]) -> dict:
    return await db.maps.find_one_and_delete(
        {
            'long': map_data['long'],
            'lat': map_data['lat']
        }
    )


# TODO: rewrite this whenever i get around to using S3
async def remove_files(post: dict):
    for f in post.get('files', []):
        if os.path.isfile(f.get('name', '')):
            os.remove(f['name'])
            if file_thumbnail := f.get('thumb'):
                if (
                    os.path.isfile(file_thumbnail)
                    and file_thumbnail != thumb_def
                    and file_thumbnail != spoilered
                ):
                    os.remove(file_thumbnail)


def synchronize_removal(post: dict):
    try:
        asyncio.run(remove_files(post))
    except (TypeError, FileNotFoundError) as e:
        print(f"failed to remove {post} with error {e}")


async def get_ip(req: HTTPServerRequest):
    return req.headers.get('X-Real-IP') or req.remote_ip


# decorator that checks if user is admin
def ifadmin(f: Callable):
    def wrapper(self, *args, **kwargs):
        if not self.user.is_admin:
            return self.redirect('/admin/login')
        return f(self, *args, **kwargs)
    return wrapper


def admin_required(f: Callable):
    def wrapper(self, *args, **kwargs):
        if not self.user.is_admin:
            return self.redirect('/admin/login')
        return f(self, *args, **kwargs)
    return wrapper


def admin_or_mod_required(f: Callable):
    def wrapper(self, *args, **kwargs):
        if not self.user.is_admin_or_moderator:
            return self.redirect('/admin/login')
        return f(self, *args, **kwargs)
    return wrapper


# TODO: rewrite blacklist as class
def save_blacklist(blacklist: list[str]):
    with open('blacklist.pkl', 'wb') as f:
        pickle.dump(list(set(blacklist)), f)


def get_blacklist() -> list[str]:
    try:
        with open('blacklist.pkl', 'rb') as f:
            return pickle.load(f)
    except (EOFError, FileNotFoundError):
        return []


def has_blacklisted_words(text: str) -> bool:
    return any([re.search(re.escape(word), text, re.IGNORECASE) for word in get_blacklist()])


def get_replies(text: str) -> list[int]:
    text = text.replace('&gt;', '>')
    replies = []
    for entry in re.finditer(re.compile(r'(>>\d+)'), text):
        number = entry.group(0)
        replies.append(int(number[2:]))
    return replies


def check_path(path: PATHLIKE):
    if not os.path.exists(path):
        os.makedirs(path)
