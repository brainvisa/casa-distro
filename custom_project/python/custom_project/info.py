# Capsul current version
version_major = 2
version_minor = 1
version_micro = 0

# Expected by setup.py: string of form "X.Y.Z"
__version__ = "{0}.{1}.{2}".format(version_major, version_minor, version_micro)

#brainvisa_dependencies = [
    #'soma-base',
    #'soma-workflow',
    #('RUN', 'RECOMMENDS', 'python-qt4', 'RUN'),
    #('RUN', 'RECOMMENDS', 'graphviz', 'RUN'),
#]


# Project description
description = "custom_project"
long_description = """
=============
Custom Project 
=============

[custom project] is a great project to illustrate how to build and share a custom project within CASA environment."""

# Main setup parameters
NAME = "custom_project"
ORGANISATION = "My lab"
MAINTAINER = "Me"
MAINTAINER_EMAIL = "me@mylab.ici"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
LICENSE = "CeCILL-B"
VERSION = __version__


