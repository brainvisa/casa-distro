# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import sys
from glob import glob
from setuptools import find_packages, setup

packages = find_packages('python')

scripts = ['bin/casa_distro', 'bin/casa_distro_admin']

here = os.path.abspath(os.path.dirname(__file__))
release_info = {}
with open(os.path.join(here, 'python', 'casa_distro', 'info.py')) as f:
    code = f.read()
    exec(code, release_info)

# Parse share directory to add extra data files in a directory
# that can be automatically found during casa_distro startup
distro_dir = os.path.join(here, 'share', 'distro')
data_files = []
for base, dirs, files in os.walk(distro_dir):
    if files:
        # data_files.extend(os.path.join(base[len(here)+1:],i) for i in files)
        data_files.append([
            os.path.join(
                'lib', 'python%d.%d' % sys.version_info[:2],
                'site-packages', 'casa_distro',
                'share', 'distro',
                base[len(distro_dir) + 1:]
            ),
            [os.path.join(base[len(here) + 1:], i) for i in files]
        ])
from pprint import pprint
pprint(data_files)

setup(
    name=release_info['NAME'],
    description=release_info['DESCRIPTION'],
    long_description=release_info['LONG_DESCRIPTION'],
    license=release_info['LICENSE'],
    author=release_info['AUTHOR'],
    author_email=release_info['AUTHOR_EMAIL'],
    version=release_info["__version__"],
    package_dir={'': 'python'},
    packages=packages,
    data_files=data_files,
    scripts=scripts,
    install_requires=[],  # we do not want casa-distro to have dependencies
)
