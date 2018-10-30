from pymongo import MongoClient
import os

from utils import *

con = MongoClient('localhost', 27017)
database = con['imageboard']

image_extensions = ["jpg", "jpeg", "png", "gif"]
video_extensions = ["webm", "mp4"]
audio_extensions = ["ogg", "mp3", "wav", "opus"]


def change_posts():
    posts = database.posts.find({})
    for post in posts:
        if not post.get('files'):
            if post.get('original'):
                filetype = None
                if post['image']: filetype = 'image'
                if post['video']: filetype = 'video'
                if post['audio']: filetype = 'audio'
                post['files'] = [{'original': post['original'],
                                'name': post[filetype],
                                'thumb': post['thumb'],
                                'filedata': post['filedata'],
                                'filetype': filetype,
                                }]
            else:
            post['files'] = []
        post.pop('original', None)
        post.pop('thumb', None)
        post.pop('filedata', None)
        post.pop('image', None)
        post.pop('video', None)
        post.pop('audio', None)
        post.pop('filetype', None)
        database.posts.replace_one({'count': post['count']}, post)

def get_extension(path):
    return os.path.splitext(path)[1].lstrip('.').lower()


def change_fucked_up():
    posts = database.posts.find({'files': {'$ne': None}})
    for p in posts:
        for f in p['files']:
            if get_extension(f['original']) in image_extensions:
                f['filetype'] = 'image'
            elif get_extension(f['original']) in video_extensions:
                f['filetype'] = 'video'
            elif get_extension(f['original']) in audio_extensions:
                f['filetype'] = 'audio'
            f['name'] = f['filename']
    database.posts.replace_one({'count': p['count']}, p)





if __name__ == '__main__':
    change_posts()
    #change_fucked_up()
