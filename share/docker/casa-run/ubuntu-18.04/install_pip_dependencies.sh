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


###############################################################################
# Install Python dependencies with pip
###############################################################################

PIP2="sudo python2 -m pip --no-cache-dir"
$PIP2 install -U pip

# APT only ships six 1.11.0 under Ubuntu 18.04
$PIP2 install 'six~=1.13'

# Runtime dependencies of populse-db
$PIP2 install 'lark-parser>=0.7'

# Runtime dependencies of Morphologist
$PIP2 install 'torch'
$PIP2 install 'torch-vision'

# Runtime dependency of datamind and Constellation
$PIP2 install http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.59.tar.gz
