# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import socket
import time
import os
import sys
import subprocess
import math
from casa_distro import six

try:
    # Try Python 3 only import
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

osp = os.path


def download_file_internal(url, dest, timeout=10., callback=None,
                           cbk_interval=0.3, allow_continue=False):
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
        callback function to display the progress of the download.
        :func:`stdout_progress` may be used.
    cbk_interval: float
        minimum interval (in seconds) between two calls to the progress
        callback. Note that in case of stalling connection, the low-level read
        function will block until the timeout is reached, and the progress
        callback is not called during this time (thus the download speed will
        not be updated)
    allow_continue: bool
        if True and if a local file already exists for output, that is smaller
        than the file to be downloaded, then assume the local file is an
        incomplete download of the same file, and append the remaining of the
        remote file.
    '''
    buffer_size = 1024 * 4
    input = urlopen(url, timeout=timeout)
    info = input.info()
    size = int(info.get('Content-Length', 0))
    dl_len = 0
    last_time = time.time()
    block = 0
    base_url = os.path.basename(url)
    last_pos = 0
    speed = 0
    cbk_count = 0
    open_mode = 'wb'
    if allow_continue and os.path.exists(dest):
        dsize = os.stat(dest).st_size
        if dsize == size:
            print('already downloaded.')
            return
        elif dsize > size:
            print('size inconsistency - downloading the whole file again')
            allow_continue = False
        else:
            open_mode = 'ab'
            headers = {'Range': 'bytes=%d-%d' % (dsize, size)}
            new_url = Request(url, headers=headers)
            input = urlopen(new_url, timeout=timeout)
            dl_len = dsize

    with open(dest, open_mode) as output:
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
                # print('*** timeout ***')
                # print('resume at:', dl_len)
                headers = {'Range': 'bytes=%d-%d' % (dl_len, size)}
                new_url = Request(url, headers=headers)
                input = urlopen(new_url, timeout=timeout)
        if callback:
            callback(base_url, dl_len, size, speed, block, cbk_count)
            print()


_term_width = 79
_term_width_timestamp = 0


def stdout_progress(url, pos, size, speed, block, count):
    ''' Print the current download progress on stdout
    '''
    global _term_width, _term_width_timestamp

    if time.time() - _term_width_timestamp >= 1.:
        try:
            _term_width = int(subprocess.check_output(
                ['stty', 'size']).split()[1]) - 1
            _term_width_timestamp = time.time()
        except subprocess.CalledProcessError:
            pass

    if _term_width >= 70:
        url_width = _term_width - 40
    else:
        url_width = _term_width - 30
    if pos > (1 << 30):
        posstr = '%.2fGB' % (float(pos) / (1 << 30))
    elif pos > (1 << 20):
        posstr = '%.2fMB' % (float(pos) / (1 << 20))
    elif pos > (1 << 10):
        posstr = '%.2fKB' % (float(pos) / (1 << 10))
    else:
        posstr = '%dB' % pos
    if size > (1 << 30):
        szstr = '%.2fGB' % (float(size) / (1 << 30))
    elif size > (1 << 20):
        szstr = '%.2fMB' % (float(size) / (1 << 20))
    elif size > (1 << 10):
        szstr = '%.2fKB' % (float(size) / (1 << 10))
    else:
        szstr = '%dB' % size
    if speed > (1 << 30):
        spstr = '%.2fGB/s' % (float(speed) / (1 << 30))
    elif speed > (1 << 20):
        spstr = '%.2fMB/s' % (float(speed) / (1 << 20))
    elif speed > (1 << 10):
        spstr = '%.2fKB/s' % (float(speed) / (1 << 10))
    else:
        spstr = '%.2fB/s' % speed
    perstr = '%d' % int((float(pos) / size) * 100) + '%'

    time_left = float(size - pos) / speed
    if time_left > 3600:
        timestr = '%dh%2dm' \
            % (int(math.floor(time_left / 3600)),
               int((time_left - math.floor(time_left / 3600) * 3600) / 60))
    elif time_left > 60:
        timestr = '%dm%2ds' \
            % (int(math.floor(time_left / 60)),
               int(time_left - math.floor(time_left / 60) * 60))
    else:
        timestr = '%ds' % int(time_left)

    length = len(url)
    if length > url_width:
        dl = len(url) - url_width
        decal = length - url_width - abs(count % (dl * 2) - dl)
        url = url[decal:decal + url_width]
    msg = '%s   %s / %s, %s' % (url, posstr, szstr, spstr)
    if _term_width - url_width > 30:
        msg += ' (%s, %s)' % (perstr, timestr)
    if len(msg) > _term_width:
        msg = msg[-_term_width:]
    else:
        msg += ' ' * (_term_width - len(msg))
    print('\r%s\r' % msg, end='')
    sys.stdout.flush()


_wget_command = None
_temporary_files = []


def _clear_temp_files():
    import shutil

    global _temporary_files

    for item in _temporary_files:
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.unlink(item)


def wget_command(download_container=True):
    '''
    Return the path of the wget command installation. If the wget program
    cannot be found, then download locally (and temporarily) a singularity
    image containing it and use it instead.

    The returned path is a list usable by subprocess.call(), ex:
    `['singularity',  run', '/tmp/wget']`

    Parameters
    ----------
    download_container: bool
        if True and wget cannot be found already installed on the system, then
        a wget container (singularity or docker) will be downloaded and used.
    '''
    global _wget_command, _temporary_files

    if _wget_command is not None:
        if _wget_command == []:
            raise RuntimeError('wget command cannot be found.')
        return _wget_command

    import distutils.spawn

    wget = distutils.spawn.find_executable('wget')
    if wget:
        _wget_command = [wget]
        return _wget_command

    if not download_container:
        raise RuntimeError('wget command cannot be found.')

    import subprocess

    wget_image = 'mwendler/wget'

    # look for singularity
    singularity = distutils.spawn.find_executable('singularity')

    if singularity:
        # create a temp repository for singularity
        import tempfile
        import atexit

        tmp_dir = tempfile.mkdtemp(prefix='casa_')
        _temporary_files.append(tmp_dir)
        atexit.register(_clear_temp_files)

        wget_path = os.path.join(tmp_dir, 'wget')
        env = dict(os.environ)
        env['SINGULARITY_CACHEDIR'] = tmp_dir
        subprocess.check_call(
            ['singularity', '--version'],
            cwd=tmp_dir, env=env)
        subprocess.check_call(
            ['singularity', 'pull', 'wget', 'docker://%s' % wget_image],
            cwd=tmp_dir, env=env)

        _wget_command = ['singularity', 'run', wget_path]

        return _wget_command

    else:

        # look for docker
        docker = distutils.spawn.find_executable('docker')

        if docker:
            subprocess.check_call(['docker', 'pull', wget_image])
            _wget_command = ['docker', 'run', '--rm', wget_image]
            return _wget_command

    _wget_command = []
    raise RuntimeError('neither wget, singularity, or docker are installed.')


def download_file(url, dest, timeout=10., callback=None, cbk_interval=0.3,
                  allow_continue=False, method='auto', use_tmp=True,
                  md5_check=None):
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
        callback function to display the progress of the download.
        :func:`stdout_progress` may be used.
    cbk_interval: float
        minimum interval (in seconds) between two calls to the progress
        callback. Note that in case of stalling connection, the low-level read
        function will block until the timeout is reached, and the progress
        callback is not called during this time (thus the download speed will
        not be updated)
    allow_continue: bool
        if True and if a local file already exists for output, that is smaller
        than the file to be downloaded, then assume the local file is an
        incomplete download of the same file, and append the remaining of the
        remote file.
    method: str
        download method to use:
        'internal': internal implementation based on urllib,
        'wget': use wget,
        'wget_no_dl': use wget from the system, don't download a container
        image for it,
        'auto': try in this order: ('wget_no_dl', 'internal', 'wget').
    use_tmp: bool
        if True, download a temporary file appended with ".part"
        ("/home/someone/file.sif" -> "/home/someone/file.sif.part") and move
        it to the final (dest) location only after the download is finished.
        This avoids erasing older files before the download is finished.
    md5_check: str
        if not None, check the md5 sum of the downloaded file and checks it
        matches the given hash string
    '''
    methods = ('internal', 'wget', 'wget_no_dl', 'auto')
    if method not in methods:
        raise ValueError('unknown download method "%s", must be in %s'
                         % (method, repr(methods)))
    used_methods = [method]

    if use_tmp:
        tmp_dest = list(osp.split(dest))
        tmp_dest[-1] = tmp_dest[-1] + '.part'
        tmp_dest = osp.join(*tmp_dest)
    else:
        tmp_dest = dest
    if method == 'auto':
        used_methods = ['wget_no_dl', 'internal', 'wget']
    done = False
    for method in used_methods:
        try:
            if method in ('wget', 'wget_no_dl'):
                if method == 'wget_no_dl':
                    wget = wget_command(download_container=False)
                else:
                    wget = wget_command()
                cmd = list(wget)
                if allow_continue:
                    cmd.append('--continue')
                cmd += [url, '-O', tmp_dest]
                subprocess.check_call(cmd)
            elif method == 'internal':
                download_file_internal(url, tmp_dest, timeout=timeout,
                                       callback=callback,
                                       cbk_interval=cbk_interval,
                                       allow_continue=allow_continue)
            done = True
            break
        except Exception:
            done = False
    if not done:
        six.reraise(sys.last_type, sys.last_value, sys.last_traceback)

    if md5_check:
        from .hash import file_hash
        if file_hash(tmp_dest) != md5_check:
            raise RuntimeError('mismatching md5 sum')
    if use_tmp:
        os.rename(tmp_dest, dest)
