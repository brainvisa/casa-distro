# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from glob import glob
import json
import os
import os.path as osp

from casa_distro import share_directories

def iter_distros():
    """
    Iterate over all available distros. For each one, yield a
    dictionary corrasponding to the casa_distro.json file
    with the "directory" item added.
    """
    for share_directory in share_directories():
        for root, dirs, files in os.walk(share_directory):
            if 'casa_distro.json' in files:
                distro = json.load(open(osp.join(root, 'casa_distro.json')))
                distro['directory'] = osp.dirname(osp.dirname(root))
                yield distro

def select_distro(distro):
    """
    Select a distro given its name or an existing distro directory.
    """
    if osp.isdir(distro):
        directory = distro
        casa_distro_json = osp.join(directory, 'host', 'conf', 'casa_distro.json')
        if osp.exists(casa_distro_json):
            distro = json.load(open(casa_distro_json))
            distro['directory'] = directory
            return distro
    else:
        for d in iter_distros():
            if d['name'] == distro:
                return d
    raise ValueError('Invalid distro: {0}'.format(distro))

_casa_distro_directory = None

def casa_distro_directory():
    """
    Return the defaut casa_distro directory.
    Either $CASA_DEFAULT_REPOSITORY or ~/casa_distro.
    """
    global _casa_distro_directory
    
    if _casa_distro_directory is None:
        _casa_distro_directory = os.environ.get('CASA_DEFAULT_REPOSITORY')
        if not _casa_distro_directory:
            _casa_distro_directory = osp.expanduser('~/casa_distro')
    return _casa_distro_directory
