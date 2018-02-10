from tornado.process import Subprocess
from tornado import gen
import logging
import json
from subprocess import Popen, PIPE
import os.path
from PIL import Image

image_extensions = ["jpg", "jpeg", "png", "gif"]
video_extensions = ["webm", "mp4"]
audio_extensions = ["ogg", "mp3"]
image_codecs = ['JPEG', 'PNG', 'GIF']
video_codecs = ['theora', 'vp8', 'vp9', 'h264', 'vp6f']
thumbnail_size = (120, 100)

def get_extension(path):
    return os.path.splitext(path)[1].lstrip('.').lower()


def get_basename(path):
    return os.path.splitext(os.path.basename(path))[0]


async def get_video_size(path):
    streams = await ffprobe(path)
    try:
        x = streams['format']['duration'].split('.')
        x[-1] = x[-1][:2]
        if int(x[0]) <= 59:
            duration = ('.').join(x) + 's'
        else:
            m, s = divmod(int(x[0]), 60)
            duration = '{0}:{1}'.format(m, s)
    except KeyError:
        duration = None
    for stream in streams['streams']:
        if stream['codec_name'] in video_codecs:
            return stream['width'], stream['height'], duration
    raise Exception("Corrupt video file")


async def ffprobe(path):
    ps = Subprocess(['ffprobe', '-print_format', 'json', '-show_format', '-show_streams', path], stdout=PIPE, stderr=PIPE)
    try:
        ret = await ps.wait_for_exit()
    except:
        raise Exception("Corrupt video file")
    stdout, stderr = ps.stdout.read(), ps.stderr.read()
    return json.loads(stdout.decode('utf-8'))


async def get_image_size(path):
    im = Image.open(path)
    width, height = im.size
    format = path.split('.')[-1].upper()
    if format == 'JPG': format = 'JPEG'
    if format not in image_codecs:
        raise Exception('Corrupt image file')
    return width, height


async def make_thumbnail(path):
    duration = None
    ex = 'jpg'
    if path.split('.')[-1].lower() == 'png' or path.split('.')[-1].lower() == 'gif':
        ex = 'png'
    tname = "uploads/{0}_thumb.{1}".format(get_basename(path), ex)
    if get_extension(path) in image_extensions:
        width, height = await get_image_size(path)
        scale = min(float(thumbnail_size[0]) / width, float(thumbnail_size[1]) / height, 1.0)
        twidth = int(scale * width)
        theight = int(scale * height)
        tsize = '%sx%s!' % (twidth, theight)
        ps = Subprocess(['convert', path+'[0]', '-thumbnail', tsize, '-strip', tname], stderr=PIPE, stdout=PIPE)
        try:
            ret = await ps.wait_for_exit()
        except:
            return 'static/missing_thumbnail.jpg'
        return tname
    elif get_extension(path) in video_extensions:
        width, height, duration = await get_video_size(path)
        scale = min(float(thumbnail_size[0]) / width, float(thumbnail_size[1]) / height, 1.0)
        twidth = int(scale * width)
        theight = int(scale * height)
        tsize = '%sx%s' % (twidth, theight)
        ps = Subprocess(['ffmpeg', '-i', path, '-y', '-s', tsize, '-vframes', '1', '-f', 'image2', '-c:v', 'mjpeg', tname], stderr=PIPE, stdout=PIPE)
        try:
            ret = await ps.wait_for_exit()
        except:
            return 'static/missing_thumbnail.jpg'
        return tname
    elif get_extension(path) in audio_extensions:
        return None
    else:
        raise Exception("Format not supported")
