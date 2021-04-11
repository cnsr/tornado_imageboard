import asyncio
import hashlib
import binascii
import os
import pickle
import re

import motor.motor_tornado
from motor.motor_tornado import MotorDatabase

thumb_def = 'static/missing_thumbnail.jpg'
spoilered = 'static/spoiler.jpg'


def generate_password(raw_password: str) -> str:
    # as an alternative, apssword hash can be stored in .env
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    password_hash = binascii.hexlify(
        hashlib.pbkdf2_hmac('sha512', raw_password.encode('utf-8'), salt, 100000)
    )
    return (salt + password_hash).decode('ascii')


def verify_password(raw_password: str, hashed_password: str) -> bool:
    return hashed_password[64:] == binascii.hexlify(
        hashlib.pbkdf2_hmac('sha512', raw_password.encode('utf-8'), hashed_password[:64].encode('ascii'), 100000)
    ).decode('ascii')


def exclude(_from: dict) -> dict:
    return {i: False for i in _from}


# updates one db entry by set parametres
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


async def check_map(db: MotorDatabase, mapdata: dict[str, str]) -> dict:
    return await db.maps.find_one_and_delete(
        {
            'long': mapdata['long'],
            'lat': mapdata['lat']
        }
    )


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
        print(post)


async def get_ip(req):
    return req.headers.get('X-Real-IP') or req.remote_ip


# decorator that checks if user is admin
def ifadmin(f):
    def wrapper(self, *args, **kwargs):
        if not self.current_user.is_admin:
            return self.redirect('/admin/login')
        return f(self, *args, **kwargs)
    return wrapper


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
    blacklist = get_blacklist()
    return any([re.search(re.escape(word), text, re.IGNORECASE) for word in blacklist])


def get_replies(text):
    text = text.replace('&gt;', '>')
    replies = []
    x = re.compile(r'(>>\d+)')
    it = re.finditer(x, text)
    for x in it:
        number = x.group(0)
        replies.append(int(number[2:]))
    return replies
