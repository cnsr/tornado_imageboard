from PIL import Image
import os
import sys
import subprocess

def video_thumb(path):
    new = path.split('.')[0] + '_thumb.jpeg'
    # this might not work if video is under 1 second long
    try:
        subprocess.call(['ffmpeg', '-i', path, '-ss', '00:00:01.000', '-vframes', '1', new], stdout=subprocess.PIPE)
        new = pic_thumb(new, v=True)
        return new
    except Exception as e:
        print(e)
        return 'static/missing_thumbnail.jpg'


def pic_thumb(path, v=False):
    if not v:
        name, ext = path.split('.')
    try:
        img = Image.open(path)
        img.thumbnail((180,180), Image.ANTIALIAS)
        if not v:
            new = name + '_thumb.' + ext
        else:
            new = path
        # resizes with optimizing filesize
        # if picture is in png you're fucked anyway lol
        img.save(new, optimize=True, quality=85)
        return new
    except IOError as e:
        print(e)
        return 'static/missing_thumbnail.jpg'
