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

# The pip_constraints.txt file is used to pin a specific version of every
# package in order to avoid unexpected breakage, while keeping this file clean.
# Please add a constraint to pip_constraints.txt if you add a package here.
#
# If there is a specific reason to constrain the version of a package, please
# introduce the version constraint in this file and document the reason.

PIP3="sudo python3 -m pip --no-cache-dir"
PIP_INSTALL="$PIP3 install -c /build/pip_constraints.txt"
${PIP_INSTALL} -U pip

# Packages not available in APT
${PIP_INSTALL} nipype
${PIP_INSTALL} dipy

# Runtime dependencies of Morphologist
${PIP_INSTALL} torch
${PIP_INSTALL} torch-vision

# Runtime dependency of Constellation
${PIP_INSTALL} http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.59.tar.gz

# ipython, jupyter, qtconsole, nbconvert
# warning: constraints specified on versions because recent versions of
# ipykernel and tornado (especially) cause the qtconsole from a running app
# to fail / hang
${PIP_INSTALL} ipykernel tornado jupyter_client \
               qtconsole nbconvert ipywidgets ipycanvas ipyevents jupyter \
               jupyterlab_widgets jupyter_console
