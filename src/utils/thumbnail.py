import json
import os.path
from subprocess import PIPE
from typing import Optional, Union

from PIL import Image
from tornado.process import Subprocess

from .func_utils import PATHLIKE, FileTypes

image_extensions = ["jpg", "jpeg", "png", "gif"]
video_extensions = ["webm", "mp4"]
audio_extensions = ["ogg", "mp3", "wav", ]

image_codecs = ['JPEG', 'PNG', 'GIF', 'jpg', 'jpeg', 'png', 'gif', 'JPG',]
video_codecs = ['theora', 'vp8', 'vp9', 'h264', 'vp6f']

thumbnail_size = (120, 100)


missing_thumbnail = 'static/missing_thumbnail.jpg'


def get_extension(path: PATHLIKE) -> str:
    return os.path.splitext(path)[1].lstrip('.').lower()


def get_basename(path: PATHLIKE) -> str:
    return os.path.splitext(os.path.basename(path))[0]


async def get_video_size(path: PATHLIKE) -> tuple[int, int, Optional[str]]:
    streams = await ffprobe(path)
    try:
        x = streams['format']['duration'].split('.')
        x[-1] = x[-1][:2]
        if int(x[0]) <= 59:
            duration = '.'.join(x) + 's'
        else:
            m, s = divmod(int(x[0]), 60)
            duration = '{0}:{1}'.format(m, s)
    except KeyError:
        duration = None
    for stream in streams['streams']:
        if stream['codec_name'] in video_codecs:
            return stream['width'], stream['height'], duration
    raise Exception("Corrupt video file")


async def ffprobe(path: PATHLIKE) -> dict[str, Union[str, list[dict[str, Union[str, int]]], dict[str, str]]]:
    ps = Subprocess(
        ['ffprobe', '-print_format', 'json', '-show_format', '-show_streams', path], stdout=PIPE, stderr=PIPE
    )
    try:
        await ps.wait_for_exit()
    except Exception as e:
        print(f"Unknown ffprobe exception: {e}")
        raise Exception("Corrupt video file")
    stdout, stderr = ps.stdout.read(), ps.stderr.read()
    return json.loads(stdout.decode('utf-8'))


async def get_image_size(path: PATHLIKE) -> tuple[int, int]:
    im = Image.open(path)
    width, height = im.size
    extension = get_extension(path)
    if extension in ('jpg', 'jpeg'):
        extension = 'JPEG'
    if extension not in image_codecs:
        raise Exception('Corrupt image file')
    return width, height


async def make_thumbnail(path: PATHLIKE) -> Optional[PATHLIKE]:
    ex = 'jpg'
    if path.split('.')[-1].lower() == 'png' or path.split('.')[-1].lower() == 'gif':
        ex = 'png'
    thumb_path = "uploads/{0}_thumb.{1}".format(get_basename(path), ex)
    if get_extension(path) in image_extensions:
        width, height = await get_image_size(path)
        scale = min(float(thumbnail_size[0]) / width, float(thumbnail_size[1]) / height, 1.0)
        thumb_sz = f'{int(scale * width)}x{int(scale * height)}!'
        ps = Subprocess(
            ['convert', path+'[0]', '-thumbnail', thumb_sz, '-strip', thumb_path], stderr=PIPE, stdout=PIPE
        )
        try:
            await ps.wait_for_exit()
        except Exception as e:
            print(f'Failed to wait for subprocess to exit: {e}')
            return missing_thumbnail
        return thumb_path
    elif get_extension(path) in video_extensions:
        width, height, duration = await get_video_size(path)
        scale = min(float(thumbnail_size[0]) / width, float(thumbnail_size[1]) / height, 1.0)
        # width x height
        thumb_sz = f'{int(scale * width)}x{int(scale * height)}'
        ps = Subprocess(
            ['ffmpeg', '-i', path, '-y', '-s', thumb_sz, '-vframes', '1', '-f', 'image2', '-c:v', 'mjpeg', thumb_sz],
            stderr=PIPE, stdout=PIPE
        )
        try:
            await ps.wait_for_exit()
        except Exception as e:
            print(f'Failed to wait for subprocess to exit: {e}')
            return missing_thumbnail
        return thumb_path
    elif get_extension(path) in audio_extensions:
        return None
    else:
        raise Exception("Format not supported")
