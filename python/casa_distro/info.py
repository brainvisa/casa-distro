import sys

# Capsul current version
version_major = 2
version_minor = 0
version_micro = 1
version_extra = ""

# The following variables are here for backward compatibility in order to
# ease a transition for bv_maker users. They will be removed in a few days.
_version_major = version_major
_version_minor = version_minor
_version_micro = version_micro
_version_extra = version_extra

# Expected by setup.py: string of form "X.Y.Z"
__version__ = "{0}.{1}.{2}{3}".format(
    version_major, version_minor, version_micro, version_extra)

# Project descriptions
description = "CASA-DISTRO"
long_description = """
========
CASA-DISTRO 
========

CASA : CATI and BrainVISA DevOps platform
CASA-DISTRO : powerful tool to manage the distribution of BrainVISA 
"""

# Main setup parameters
NAME = "casa-distro"
ORGANISATION = "CEA"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
BRAINVISA_BUILD_MODEL='pure_python'
LICENSE='CeCILL-B'
AUTHOR = 'team'
AUTHOR_EMAIL = 'nobody@x.y'
