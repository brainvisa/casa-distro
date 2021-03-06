#! /bin/bash
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
