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
# Install Python dependencies with pip
###############################################################################

# TODO: introduce a constraints.txt file as a mechanism to pin specific
# versions, while keeping this file clean.

PIP3="sudo python3 -m pip --no-cache-dir"
$PIP3 install -U pip

# Packages not available in APT
$PIP3 install nipype
$PIP3 install dipy

# Runtime dependencies of Morphologist
$PIP3 install torch
$PIP3 install torch-vision

# Runtime dependency of Constellation
$PIP3 install http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.59.tar.gz
