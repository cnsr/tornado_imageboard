import motor.motor_tornado
import os

thumb_def = 'static/missing_thumbnail.jpg'
spoilered = 'static/spoiler.jpg'

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
    if post['filetype']:
        if os.path.isfile(post[post['filetype']]):
            os.remove(post[post['filetype']])
            if post['thumb']:
                if post['thumb'] != thumb_def and post['thumb'] != spoilered:
                    os.remove(post['thumb'])


def sync_removeing(post):
    try:
        if post['filetype']:
            if os.path.isfile(post[post['filetype']]):
                os.remove(post[post['filetype']])
                if post['thumb']:
                    if post['thumb'] != thumb_def and post['thumb'] != spoilered:
                        os.remove(post['thumb'])
    except:
        print(post)


async def get_ip(req):
    x_real_ip = req.headers.get('X-Real-IP')
    return x_real_ip or req.remote_ip

