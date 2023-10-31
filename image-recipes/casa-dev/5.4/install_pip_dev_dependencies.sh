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

# Python packages that do not exist as APT packages
$PIP3 install pre-commit

# used in colorado
$PIP3 install "sphinx<7" sphinx_rtd_theme

# used to make graphs in docs
$PIP3 install sphinxcontrib-mermaid
