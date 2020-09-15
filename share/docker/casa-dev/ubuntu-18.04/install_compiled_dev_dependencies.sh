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
PY_S=3.6 PY=3.6m /opt/build_sip_pyqt.sh

# Install singularity in the image in order to run tests using
# singularity-in-singularity.
/opt/build_singularity_3.sh


# Post-install configuration
sudo ldconfig
