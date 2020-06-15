# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from glob import glob
import json
import os
import os.path as osp

from casa_distro import share_directories

def iter_distros():
    for share_directory in share_directories():
        for root, dirs, files in os.walk(share_directory):
            if 'casa_distro.json' in files:
                distro = json.load(open(osp.join(root, 'casa_distro.json')))
                distro['directory'] = osp.dirname(osp.dirname(root))
                yield distro
