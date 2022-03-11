#! /bin/bash
#
# Install dependencies for image casa-run-5.1. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image contains Python 3 and Qt 5
#
# NOTE: This script is run during the creation of the Singularity and
# VirtualBox casa-run image. Make sure not to include anything specific to a
# given virtualization/containerization engine  in this file.

set -e  # stop the script on error
set -x  # display commands before running them

###############################################################################
# Clean up build dependencies that were required for
# install_pip_dependencies.sh and install_compiled_dependencies.sh
###############################################################################

# Defines the build_dependencies bash array variable, which is used at the
# bottom of this script (see below). The build_dependencies.sh file is expected
# to be found in the same directory as this script.
. "$(dirname -- "$0")"/build_dependencies.sh

# Mark build dependencies as automatically installed, so that 'apt-get
# autoremove' will remove them.
export DEBIAN_FRONTEND=noninteractive
# -E option allow to pass environment variables through sudo
sudo -E apt-mark auto ${build_dependencies[@]}
sudo -E apt-get -o APT::Autoremove::SuggestsImportant=0 \
                autoremove --yes

###############################################################################
# set python3 as default "python" command since python2 is not installed
###############################################################################

$SUDO update-alternatives --install /usr/bin/python python /usr/bin/python3.6 10
