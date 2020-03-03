#! /bin/sh
#
# Install system dependencies for image cati/casa-test:ubuntu-18.04.
#
# NOTE: This script is used to create the casa-test Docker/Singularity image,
# and also during the creation of the VirtualBox casa-run image. Make sure not
# to include anything Docker-specific in this file.

set -e
set -x

if [ $(id -u) -eq 0 ]; then
    SUDO=
    APT_GET=apt-get
else
    SUDO=sudo
    APT_GET="sudo apt-get"
fi

###############################################################################
# Install system packages with apt-get
###############################################################################

export DEBIAN_FRONTEND=noninteractive
APT_GET_INSTALL="$APT_GET install --no-install-recommends -y"

$APT_GET update

# WARNING: it is necessary to call apt-get install separately for small groups
# of packages to avoid the mysterious 101st package issue (Download of the
# 101st package fails randomly in NeuroSpin, maybe due to firewall issues).

# Dependencies of headless Anatomist
$APT_GET_INSTALL xvfb libx11-xcb1 libfontconfig1 libdbus-1-3 libxrender1
$APT_GET_INSTALL libglib2.0-0 libxi6 x11-utils mesa-utils

# Runtime dependencies of FSL
$APT_GET_INSTALL bc dc tcsh

# General utilities
$APT_GET_INSTALL sudo wget

# VirtualGL is also a dependency of headless Anatomist
cd /tmp
# Apparently the Ubuntu base image does not contain the Let's Encrypt root
# certificate, so we have to resort to using --no-check-certificate...
wget --no-check-certificate https://sourceforge.net/projects/virtualgl/files/2.6.3/virtualgl_2.6.3_amd64.deb
$APT_GET_INSTALL libglu1-mesa  # dependency of virtualgl
$SUDO dpkg -i virtualgl_2.6.3_amd64.deb
rm -f /tmp/virtualgl_2.6.3_amd64.deb

$APT_GET clean
# delete all the apt list files since they're big and get stale quickly
$SUDO rm -rf /var/lib/apt/lists/*


###############################################################################
# Post-install configuration
###############################################################################

$SUDO ldconfig

# Create casa mount points for singularity compatibility
$SUDO mkdir -p /casa/home \
               /casa/pack \
               /casa/install \
               /casa/tests

# FIXME: there must be a safer way, check if this is really needed
$SUDO chmod 777 /casa \
          /casa/home \
          /casa/pack \
          /casa/install \
          /casa/tests
