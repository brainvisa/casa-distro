# -*- coding: utf-8 -*-
from __future__ import print_function

import os

try:
    # Python 2 imports
    from urllib import urlopen, urlretrieve
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3 imports
    from urllib.request import urlopen, urlretrieve
    from html.parser import HTMLParser

class ListdirHTMLParser(HTMLParser):
    '''
    Class used by url_listdir to extract
    the list of file entries returned by
    Apache for an URL corresponding to a
    directory.
    '''
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_td = False
        self.record_data = False
        self.listdir = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.in_td = True
        if self.in_td and tag == 'a':
            self.record_data = True

    def handle_endtag(self, tag):
        if tag == 'td':
            self.in_td = False
        elif tag == 'a':
            self.record_data = False

    def handle_data(self, data):
        if self.record_data:
            self.listdir.append(data)

def url_listdir(url):
    '''
    Return the list of file or directory entries given a web URL corresponding
    to a directory. This function is specialized in parsing directories as 
    returned by an Apache server when no index.html file is present.
    '''
    parser = ListdirHTMLParser()
    parser.feed(urlopen(url).read().decode('utf8'))
    return parser.listdir[1:]

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

def wget_command():
    '''
    Return the path of the wget command installation. If the wget program
    cannot be found, then download locally (and temporarily) a singularity
    image containing it and use it instead.

    The returned path is a list usable by subprocess.call(), ex:
    `['singularity',  run', '/tmp/wget']`
    '''
    global _wget_command, _temporary_files

    if _wget_command is not None:
        return _wget_command

    import distutils.spawn

    wget = distutils.spawn.find_executable('wget')
    if wget:
        _wget_command = [wget]
        return _wget_command

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

    raise RuntimeError('neither wget, singularity, or docker are installed.')
