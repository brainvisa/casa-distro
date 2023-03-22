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

if [ $(id -u) -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

###############################################################################
# Install Python dependencies with pip
###############################################################################

# The pip_constraints.txt file is used to pin a specific version of every
# package in order to avoid unexpected breakage, while keeping this file clean.
# Please add a constraint to pip_constraints.txt if you add a package here.
#
# If there is a specific reason to constrain the version of a package, please
# introduce the version constraint in this file and document the reason.

PIP3="$SUDO python3 -m pip --no-cache-dir"
PIP_INSTALL="$PIP3 install -c /build/pip_constraints.txt"
${PIP_INSTALL} -U pip

# soma-base v3 needs pydantic >= 1.9, ubuntu 22/apt ships 1.8
${PIP_INSTALL} -U "pydantic>=1.9"

# Capsul v3 needs redis-py >= 4.2, Ubuntu 22/apt ships 3.5.3
${PIP_INSTALL} -U "redis>=4.2"

# Packages not available in APT
${PIP_INSTALL} nipype
${PIP_INSTALL} dipy

# Runtime dependencies of soma-base
${PIP_INSTALL} pycryptodome

# Runtime dependencies of Morphologist
${PIP_INSTALL} torch --extra-index-url https://download.pytorch.org/whl/cu116
${PIP_INSTALL} torch-vision --extra-index-url https://download.pytorch.org/whl/cu116

# Runtime dependency of Constellation
${PIP_INSTALL} http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.59.tar.gz

# ipython, jupyter, qtconsole, nbconvert
# warning: constraints specified on versions because recent versions of
# ipykernel and tornado (especially) cause the qtconsole from a running app
# to fail / hang
${PIP_INSTALL} -U ipykernel tornado jupyter_client \
               qtconsole nbconvert ipywidgets ipycanvas ipyevents jupyter \
               jupyterlab_widgets jupyter_console notebook
# override nbconvert (5.6 doesn't work but notebook 5.7 requires nbconvert<6)
${PIP_INSTALL} -U 'nbconvert<6.4'

# post-install: register jupyter extensions
$SUDO jupyter nbextension enable --py widgetsnbextension
$SUDO jupyter nbextension enable --py ipyevents
$SUDO jupyter nbextension enable --py ipycanvas

# Runtime PyQt6
${PIP_INSTALL} PyQt6 PyQt6-sip PyQt6-WebEngine

# useful tool: pip search has stopped working, but pip_search works
${PIP_INSTALL} pip-search

# used by fold dico tools (deep_folding etc)
$PIP3 install 'pqdm' 'GitPython'

# used for GLTF, GLB 3D formats support
# (+ DracoPy which will be compiled in install_compiled_dependencies.sh)
$PIP3 install "webp" "pygltflib"

# fix tornado for python 3.10
$SUDO sed -i s/collections.MutableMapping/collections.abc.MutableMapping/ /usr/local/lib/python3.10/dist-packages/tornado/httputil.py
