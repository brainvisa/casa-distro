#! /bin/sh
#
# Install dependencies for image cati/casa-run:ubuntu-18.04. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image contains Python 2 and Qt 5.
#
# NOTE: This script is also run during the creation of the VirtualBox casa-run
# image. Make sure not to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them

APT_GET="sudo apt-get"

###############################################################################
# Clean up build dependencies that were required for
# install_pip_dependencies.sh and install_compiled_dependencies.sh
###############################################################################

# These are the packages that are installed at the end of
# install_apt_dependencies.sh.
$APT_GET purge -y autoconf automake cmake g++ gcc git libc-dev
$APT_GET purge -y libhdf5-dev libjxr-dev libopenjp2-7-dev libpython2.7-dev
$APT_GET purge -y libtiff-dev
$APT_GET purge -y libtool make patch pkg-config

# Remove dependencies of the above packages
$APT_GET autoremove -y --purge
$APT_GET -o APT::Autoremove::RecommendsImportant=0 \
         -o APT::Autoremove::SuggestsImportant=0 \
         autoremove -y --purge
