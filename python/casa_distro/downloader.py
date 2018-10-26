
from __future__ import print_function
try:
    # Try Python 3 only import
    import urllib.request as urllib2
except ImportError:
    import urllib2
import socket
import time
import os
import sys
import subprocess


def download_file(url, dest, timeout=10., callback=None, cbk_interval=0.3):
    '''
    Download a file from the given URL to the local path ``dest``.

    The function detects stalled downloads (after a given timeout) and retries
    the connection and continues where it stopped.

    A callback can be used to display the download progress. The builtin
    function :func:`stdout_progress` may be used for that. The function will
    receive 5 arguments:

    url:
        short URL (basename)
    pos:
        current position
    size:
        size of the file
    speed:
        instant speed in bytes/second
    block: number of blocks read since the beginning of file
    count: count of the number of calls to the callback function

    Parameters
    ----------
    url: str
        URL of the file to be downloaded
    dest: str
        output filename for the downloaded file
    timeout: float
        connection / stall timeout. After this timeout, the connection is
        closed and reoopened.
    callback: function
        callbackl function to display the progress of the download.
        :func:`stdout_progress` may be used.
    cbk_interval: float
        minimum interval (in seconds) between two calls to the progress
        callback. Note that in case of stalling connection, the low-level read
        function will block until the timeout is reached, and the progress
        callback is not called during this time (thus the download speed will
        not be updated)
    '''
    buffer_size = 1024 * 4
    input = urllib2.urlopen(url, timeout=timeout)
    info = input.info()
    size = int(info.get('Content-Length', 0))
    dl_len = 0
    last_time = time.time()
    block = 0
    base_url = os.path.basename(url)
    last_pos = 0
    speed = 0
    cbk_count = 0
    with open(dest,'wb') as output:
        while True:
            try:
                buffer = input.read(buffer_size)
                if buffer:
                    output.write(buffer)
                    dl_len += len(buffer)
                    if callback and time.time() - last_time >= cbk_interval:
                        speed = (dl_len - last_pos) / (time.time() - last_time)
                        last_pos = dl_len
                        last_time = time.time()
                        callback(base_url, dl_len, size, speed, block,
                                 cbk_count)
                        cbk_count += 1
                block += 1
                if len(buffer) < buffer_size:
                    break
            except socket.timeout:
                #print('*** timeout ***')
                #print('resume at:', dl_len)
                if size == 0:
                    s = 10000000000
                headers={'Range': 'bytes=%d-%d' % (dl_len, size)}
                new_url = urllib2.Request(url, headers=headers)
                input = urllib2.urlopen(new_url, timeout=timeout)
        if callback:
            callback(base_url, dl_len, size, speed, block, cbk_count)
            print()

def stdout_progress(url, pos, size, speed, block, count):
    ''' Print the current download progress on stdout
    '''
    term_width = 79
    try:
        term_width = int(subprocess.check_output(['stty', 'size']).split()[1]) - 1
    except:
        term_width = 80
    url_width = term_width - 30
    if pos > (1<<30):
        posstr = '%.2fGB' % (float(pos) / (1<<30))
    elif pos > (1<<20):
        posstr = '%.2fMB' % (float(pos) / (1<<20))
    elif pos > (1<<10):
        posstr = '%.2fKB' % (float(pos) / (1<<10))
    else:
        posstr = '%dB' % pos
    if size > (1<<30):
        szstr = '%.2fGB' % (float(size) / (1<<30))
    elif size > (1<<20):
        szstr = '%.2fMB' % (float(size) / (1<<20))
    elif size > (1<<10):
        szstr = '%.2fKB' % (float(size) / (1<<10))
    else:
        szstr = '%dB' % size
    if speed > (1<<30):
        spstr = '%.2fGB/s' % (float(speed) / (1<<30))
    elif speed > (1<<20):
        spstr = '%.2fMB/s' % (float(speed) / (1<<20))
    elif speed > (1<<10):
        spstr = '%.2fKB/s' % (float(speed) / (1<<10))
    else:
        spstr = '%.2fB/s' % speed
    l = len(url)
    if l > url_width:
        dl = len(url) - url_width
        decal = l - url_width - abs(count % (dl * 2) - dl)
        url = url[decal:decal + url_width]
    msg = '%s   %s / %s, %s' % (url, posstr, szstr, spstr)
    if len(msg) > term_width:
        msg = msg[-term_width:]
    else:
        msg += ' ' * (term_width - len(msg))
    print('\r%s\r' % msg, end='')
    sys.stdout.flush()



