#! /bin/sh
# Install system dependencies for image cati/casa-dev:ubuntu-16.04
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them


###############################################################################
# Compile and install dependencies that are must be built from source
###############################################################################

# reinstall an older sip and PyQt5 from sources because of a bug in sip 4.19
# and virtual C++ inheritance. The same versions are compiled for Python 2 in
# the casa-run image.
PY_S=3.6 PY=3.6m /tmp/build_sip_pyqt.sh


# Install Qt Installer Framework (prebuilt on Mandriva 2008)
cd /tmp
wget http://brainvisa.info/static/qt_installer-1.6.tar.gz
cd /usr/local
sudo tar xfz /tmp/qt_installer-1.6.tar.gz
sudo ln -s qt_installer-1.6 qt_installer
cd /usr/local/bin
sudo ln -s ../qt_installer/bin/* .
rm /tmp/qt_installer-1.6.tar.gz


# Post-install configuration
sudo ldconfig
