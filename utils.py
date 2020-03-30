import motor.motor_tornado
import os
import pickle
import re

thumb_def = 'static/missing_thumbnail.jpg'
spoilered = 'static/spoiler.jpg'

def exclude(_from):
    return {i: False for i in _from}

# updates one db entry by set parametres
async def update_db(db, count, variables):
    await db.posts.update_one(
        {'count': count},
        {
            '$set': variables
        },
        upsert=False,
    )


# for updating board data
async def update_db_b(db, short, variables):
    await db.boards.update_one(
        {'short': short},
        {
            '$set': variables
        },
        upsert=False,
    )


async def check_map(db, mapdata):
    exists = await db.maps.find_one({
                'long': mapdata['long'],
                'lat': mapdata['lat']})
    if exists:
        await db.maps.delete_one({
                'long': mapdata['long'],
                'lat': mapdata['lat']})


async def removeing(post):
    if post['files']:
        for f in post['files']:
            if os.path.isfile(f['name']):
                os.remove(f['name'])
                if f['thumb']:
                    if f['thumb'] != thumb_def and f['thumb'] != spoilered:
                        os.remove(f['thumb'])


def sync_removeing(post):
    try:
        if post['files']:
            for f in post['files']:
                if os.path.isfile(f['name']):
                    os.remove(f['name'])
                    if f['thumb']:
                        if f['thumb'] != thumb_def and f['thumb'] != spoilered:
                            os.remove(f['thumb'])
    except:
        print(post)


async def get_ip(req):
    x_real_ip = req.headers.get('X-Real-IP')
    return x_real_ip or req.remote_ip


# decorator that checks if user is admin
def ifadmin(f):
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            return self.redirect('/admin/login')
        return f(self, *args, **kwargs)
    return wrapper


def save_blacklist(blacklist):
    # clean up duplicates
    blacklist = list(set(blacklist))
    with open('blacklist.pkl', 'wb') as f:
        pickle.dump(blacklist, f)


def get_blacklist():
    try:
        with open('blacklist.pkl', 'rb') as f:
            blacklist = pickle.load(f)
        return blacklist
    except (EOFError, FileNotFoundError):
        return []


def has_blacklisted_words(text):
    blacklist = get_blacklist()
    for word in blacklist:
        found = re.search(re.escape(word), text, re.IGNORECASE)
        if found is not None: return True
    return False

