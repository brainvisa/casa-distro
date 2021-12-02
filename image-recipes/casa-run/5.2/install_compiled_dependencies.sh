#! /bin/sh
#
# Install dependencies for image casa-run-5.1. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image supports a Python 3 / Qt 5 build of BrainVISA.
#
# NOTE: This script is run during the creation of the Singularity and
# VirtualBox casa-run image. Make sure not to include anything specific to a
# given virtualization/containerization engine  in this file.

set -e  # stop the script on error
set -x  # display commands before running them


###############################################################################
# Compile and install dependencies that are must be built from source
###############################################################################

# MIRCen's fork of openslide with support for CZI format
cd /tmp
git clone --depth=1 https://github.com/MIRCen/openslide.git
cd openslide
autoreconf --install
./configure
make -j$(nproc)
sudo make install
cd /tmp
rm -rf openslide


###############################################################################
# Post-install configuration
###############################################################################

sudo ldconfig
