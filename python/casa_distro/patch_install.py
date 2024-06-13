# -*- coding: utf-8 -*-

from casa_distro.web import url_listdir, urlopen
import os
import os.path as osp
import urllib
from dateutil import parser as tparser
import stat


def check_rw_install(install_dir='/casa/host/install'):
    print('check_rw_install')
    test_file = osp.join(install_dir, 'test')
    try:
        # check the install dir contains something
        with open(osp.join(install_dir, 'python/soma/info.py')) as f:
            f.read()
        # check the install dir is writable
        with open(test_file, 'w') as f:
            f.write('test\n')
        os.unlink(test_file)

        return True
    except Exception:
        raise RuntimeError('Read-write installation is not available')


def get_distro_version():
    try:
        from soma import info
        version = info.__version__
    except ImportError:
        version = '5.1.0'
    return version


def list_updates(patches_url='https://brainvisa.info/download/updates',
                 version=None, install_dir='/casa/host/install'):
    if version is None:
        version = get_distro_version()
    url = '%s/%s' % (patches_url, version)
    done = []
    try:
        todo = ['%s/%s' % (url, urllib.parse.quote(fname))
                for fname in url_listdir(url)]
    except urllib.error.HTTPError:
        return  # no patches for this version
    while todo:
        item = todo.pop(0)
        if item.endswith('/'):  # directory
            todo += ['%s%s' % (item, urllib.parse.quote(fname))
                     for fname in url_listdir(item)]
        else:
            rel_fname = urllib.parse.unquote(item[len(url):])
            install_fname = install_dir + rel_fname
            resp = urlopen(item)
            dt = tparser.parse(resp.getheader('Last-Modified'))
            t = dt.timestamp()
            if osp.exists(install_fname):
                d = os.stat(install_fname).st_mtime
                if d >= t:
                    # up to date
                    continue
            done.append(install_fname)
    return done


def patch_install(patches_url='https://brainvisa.info/download/updates',
                  version=None, install_dir='/casa/host/install'):
    if version is None:
        version = get_distro_version()
    url = '%s/%s' % (patches_url, version)
    done = []
    try:
        todo = ['%s/%s' % (url, urllib.parse.quote(fname))
                for fname in url_listdir(url)]
    except urllib.error.HTTPError:
        return  # no patches for this version
    while todo:
        item = todo.pop(0)
        if item.endswith('/'):  # directory
            todo += ['%s%s' % (item, urllib.parse.quote(fname))
                     for fname in url_listdir(item)]
        else:
            # print('download:', item)
            rel_fname = urllib.parse.unquote(item[len(url):])
            install_fname = install_dir + rel_fname
            # print('install to:', install_fname)
            resp = urlopen(item)
            dt = tparser.parse(resp.getheader('Last-Modified'))
            t = dt.timestamp()
            if osp.exists(install_fname):
                d = os.stat(install_fname).st_mtime
                if d >= t:
                    # up to date
                    # print('up to date')
                    continue
            print('download:', item, 'to:', install_fname)
            file_content = resp.read()
            if not osp.exists(osp.dirname(install_fname)):
                # print('mkdir', osp.dirname(install_fname))
                os.makedirs(osp.dirname(install_fname))
            with open(install_fname, 'wb') as f:
                f.write(file_content)
            # set timestamp
            os.utime(install_fname, (t, t))
            # can we get the +x status from request ?
            mod = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
            if item.startswith('%s/bin/' % url):
                mod |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            os.chmod(install_fname, mod)
            done.append(install_fname)
    return done


if __name__ == '__main__':
    check_rw_install()
    updated = patch_install()
    print('updated files:', updated)
