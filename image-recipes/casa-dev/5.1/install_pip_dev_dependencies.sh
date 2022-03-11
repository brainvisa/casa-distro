#! /bin/sh
# Install system dependencies for image casa-dev-5.0
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them


###############################################################################
# Install Python dependencies with pip
###############################################################################

# General note: some packages are prevented from being upgraded by appending
# the '<x.y.z' version requirement. Unless noted otherwise, this is done solely
# to prevent accidental breakage during image rebuilds, when new PyPI versions
# introduce incompatible changes. These version blocks should be revised
# regularly!

SUDO="sudo"
PIP3="sudo python3 -m pip --no-cache-dir"
PIP_INSTALL="$PIP3 install -c /opt/pip_constraints.txt"

# Tool to handle multiple git/svn repositories
$PIP_INSTALL 'vcstool'

# Development tools are most useful if installed in a recent version by pip,
# even if they are available as APT packages
$PIP_INSTALL modernize  # can be removed when all Python2-only code is gone
$PIP_INSTALL --ignore-installed PyYAML pre-commit
$PIP_INSTALL tox
