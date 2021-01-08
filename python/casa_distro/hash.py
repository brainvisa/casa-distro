# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import hashlib
import os


def file_hash(path, blocksize=2**20):
    m = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def check_hash(path, md5_file):
    if os.path.isfile(path):
        hashsum = file_hash(path)
    else:
        hashsum = path
    recorded_hash = open(md5_file).read().strip().split()[0]
    return hashsum == recorded_hash
