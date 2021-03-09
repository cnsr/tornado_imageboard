import json
import shlex
import subprocess


# function to find the resolution of the input video file
def resolution(pathToInputVideo):
    cmd = "ffprobe -v quiet -print_format json -show_streams"
    args = shlex.split(cmd)
    args.append(pathToInputVideo)
    # run the ffprobe process, decode stdout into utf-8 & convert to JSON
    ffprobeOutput = subprocess.check_output(args).decode('utf-8')
    ffprobeOutput = json.loads(ffprobeOutput)

    # prints all the metadata available:
    #import pprint
    #pp = pprint.PrettyPrinter(indent=2)
    #pp.pprint(ffprobeOutput)

    # for example, find height and width
    # return zeros if there is no such data
    try:
        height = ffprobeOutput['streams'][0]['height']
        width = ffprobeOutput['streams'][0]['width']
    except:
        height = width = 0

    return width, height
