#! /bin/sh
# Install system dependencies for image casa-dev-5.1
#
# NOTE: This script is run during the creation of the Singularity and
# VirtualBox casa-run image. Make sure not to include anything specific to a
# given virtualization/containerization engine  in this file.

set -e  # stop the script on error
set -x  # display commands before running them

if [ $(id -u) -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

###############################################################################
# Install Python dependencies with pip
###############################################################################

# TODO: introduce a constraints.txt file as a mechanism to pin specific
# versions, while keeping this file clean.

PIP3="$SUDO python3 -m pip --no-cache-dir"
PIP_INSTALL="$PIP3 install -c /build/pip_dev_constraints.txt"

# Python packages that do not exist as APT packages
$PIP_INSTALL pre-commit

# sphinx_rtd_theme needs docutils <0.19,
# sphinxcontrib-mermaid needs >=0.18.1 in order to avoid a bug
# apt ships 0.17.1 which is not good enough
$PIP_INSTALL -U "docutils<0.19"

# used in colorado
$PIP_INSTALL sphinx sphinx_rtd_theme

# used to make graphs in docs
$PIP_INSTALL sphinxcontrib-mermaid

# used in populse_mia docs
$PIP_INSTALL myst-parser

$PIP_INSTALL 'sip>6'
