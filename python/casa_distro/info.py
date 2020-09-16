# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys

# casa-distro version
version_major = 3
version_minor = 0
version_micro = 0
version_extra = ""

short_version = '{0}.{1}'.format(version_major, version_minor)

# Expected by setup.py: string of form "X.Y.Z"
__version__ = '{0}.{1}.{2}{3}'.format(
    version_major, version_minor, version_micro, version_extra)

# Build model required for brainvisa-cmake
BRAINVISA_BUILD_MODEL = 'pure_python'

# Project descriptions
NAME = "casa-distro"
DESCRIPTION = ('Framework to compile and distribute BrainVISA distributions')
LONG_DESCRIPTION = '''
===========
casa-distro
===========

Casa-distro package is the user component of a BrainVISA project allowing to
distribute containers containing standard compilation environements for
various BrainVISA distributions.
'''
LICENSE = 'CeCILL-B'
AUTHOR = 'BrainVISA team'
AUTHOR_EMAIL = 'contact@brainvisa.info'
