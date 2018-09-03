from __future__ import print_function

import os
import sys
from glob import glob
from setuptools import find_packages, setup

# Select appropriate modules
modules = find_packages('python')

scripts = ['bin/casa_distro']

here = os.path.abspath(os.path.dirname(__file__))
release_info = {}
with open(os.path.join(here, 'python', 'casa_distro', 'info.py')) as f:
    code = f.read()
    exec(code, release_info)

distro_dir = os.path.join(here, 'share', 'distro')
share_dir = 'casa-distro-%s' % release_info['short_version']
data_files = []
for base, dirs, files in os.walk(distro_dir):
    if files:
        data_files.append([os.path.join('share', share_dir, 'distro', base[len(distro_dir)+1:]), [os.path.join(base,i) for i in files]])
    print(base, dirs, files)
    

# Build the setup
setup(
    name=release_info["NAME"],
    description=release_info["DESCRIPTION"],
    long_description=release_info["LONG_DESCRIPTION"],
    license=release_info["LICENSE"],
    #classifiers=release_info["CLASSIFIERS"],
    #author=release_info["AUTHOR"],
    #author_email=release_info["AUTHOR_EMAIL"],
    version=release_info["__version__"],
    #url=release_info["URL"],
    package_dir={'': 'python'},
    packages=modules,
    #package_data=pkgdata,
    #platforms=release_info["PLATFORMS"],
    #extras_require=release_info["EXTRA_REQUIRES"],
    #install_requires=release_info["REQUIRES"],
    scripts=scripts,
    data_files=data_files,
    install_requires=['six'],
)
