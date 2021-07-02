import json
import os
import shlex
import subprocess
import uuid
from typing import Optional

from PIL import Image

import src.ib_settings as default_settings

from .func_utils import PATHLIKE, FileTypes, get_filetype

uploads = default_settings.UPLOAD_ROOT


async def upload_file(
    file_to_upload: dict[str, str]
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    filename = file_to_upload.get('filename')
    filetype = get_filetype(filename)
    extension = os.path.splitext(filename)[-1].lower()
    if filetype is FileTypes.UNKNOWN:
        return None, None, None, None
    new_name = os.path.join(uploads, f"{uuid.uuid4().hex}{extension}")
    with open(new_name, 'wb') as nf:
        nf.write(bytes(file_to_upload.get('body')))
    filedata = await process_file(new_name)
    return (
        filename, new_name, filetype.value, filedata
    )


async def convert_bytes(num: float):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


async def process_file(filepath: PATHLIKE) -> Optional[str]:
    if os.path.isfile(filepath):
        filesize = await convert_bytes(os.stat(filepath).st_size)
        extension = os.path.splitext(filepath)[-1].upper()
        file_type = get_filetype(filepath)
        if file_type is FileTypes.VIDEO:
            w, h = resolution(filepath)
        elif file_type is FileTypes.IMAGE:
            with Image.open(filepath) as img:
                w, h = img.size
        elif file_type is FileTypes.AUDIO:
            return f'{extension}, {filesize}'
        else:
            return None
        return f'{extension}, {w}x{h}, {filesize}'
    return None


# function to find the resolution of the input video file
def resolution(video_path: PATHLIKE) -> tuple[int, int]:
    # TODO: find a way to not be dependant on ffmpeg
    cmd = "ffprobe -v quiet -print_format json -show_streams"
    args = shlex.split(cmd)
    args.append(video_path)
    # run the ffprobe process, decode stdout into utf-8 & convert from JSON
    ffprobe_output = json.loads(subprocess.check_output(args).decode('utf-8'))

    # find height and width
    # return zeros if there is no such data
    try:
        height = ffprobe_output['streams'][0]['height']
        width = ffprobe_output['streams'][0]['width']
    except (IndexError, KeyError):
        height = width = 0

    return width, height
