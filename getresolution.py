import subprocess

def resolution(path):
    x = subprocess.Popen(
                        ['mediainfo', '--Inform=Video;%Width%x%Height%', path],
                        stdout=subprocess.PIPE,
                        encoding='utf8'
    )
    d = x.communicate()[0].strip('\n').split('x')
    return d[0], d[1]
