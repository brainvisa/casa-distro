from __future__ import print_function

import hashlib

def file_hash(path, blocksize=2**20):
    m = hashlib.md5()
    with open(path , 'rb') as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()
