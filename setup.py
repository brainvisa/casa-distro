from __future__ import print_function

import os
import sys
from glob import glob
from setuptools import find_packages, setup

packages = find_packages('python')

scripts = ['bin/casa_distro']

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
        data_files.append([os.path.join('share', 'distro', base[len(distro_dir)+1:]), [os.path.join(base,i) for i in files]])    

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
    scripts=scripts,
    data_files=data_files,
    install_requires=['six'],
)
