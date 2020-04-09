#! /bin/sh
# Install system dependencies for image cati/casa-dev:ubuntu-18.04
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them


###############################################################################
# Install Python dependencies with pip
###############################################################################


# pip3 modules should be installed first, then some commands
# (/usr/local/bin/jupyter* for instance) will be replaced by python2
# equivalents when installed by pip2. jupyter modules especially handle
# these conflicts very badly.

PIP3="sudo python3 -m pip --no-cache-dir"
$PIP3 install -U pip

# APT only ships six 1.11.0 under Ubuntu 18.04
$PIP3 install 'six~=1.13'

# Python 3 packages that do not exist as APT packages
$PIP3 install dipy
$PIP3 install nipype
$PIP3 install jenkinsapi

# Development tools are most useful if installed in a recent version by pip,
# even if they are available as APT packages
$PIP3 install modernize
$PIP3 install pre-commit
$PIP3 install tox


# Re-install the 'pip' binary to point to pip2 (pip3 upgrade can overwrite it
# with the Python 3 version).
PIP2="sudo python2 -m pip --no-cache-dir"
$PIP2 install -U --force-reinstall pip
