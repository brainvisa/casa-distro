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

SUDO="sudo"
PIP3="sudo python3 -m pip --no-cache-dir"
PIP_INSTALL="$PIP3 install -c /opt/pip_constraints.txt"
${PIP_INSTALL} -U pip

# APT only ships six 1.11.0 under Ubuntu 18.04
$PIP_INSTALL 'six~=1.13'

# Python 3 packages that do not exist as APT packages
$PIP_INSTALL 'dipy'
$PIP_INSTALL 'nipype'

# Runtime dependencies of populse-db
$PIP_INSTALL 'lark-parser>=0.7,<0.8'

# Runtime dependencies of Morphologist
$PIP_INSTALL 'torch'
$PIP_INSTALL 'torch-vision'

# Runtime dependency of datamind and Constellation
$PIP_INSTALL http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.59.tar.gz

# Under Ubuntu 18.04 APT supplies numpy 1.13.3 and scipy 0.19.1, which are
# apparently too old for our friends of the MeCA group in Marseille.
# Unfortunately installing the newer NumPy installed with pip is
# ABI-incompatible with the system NumPy (ABI version 9 vs ABI version 8), so
# we need to also install every package that depends on NumPy with pip.
$PIP_INSTALL 'numpy~=1.16,<1.17'
$PIP_INSTALL fastcluster
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
sudo CPPFLAGS='-I/usr/include/mpi' python3 -m pip --no-cache-dir install --no-binary=h5py 'h5py<2.10'
$PIP_INSTALL matplotlib
$PIP_INSTALL 'scipy~=1.2,<1.3'
$PIP_INSTALL scikit-image
$PIP_INSTALL 'scikit-learn<0.21'

# python-pcl is installed in install_compiled_dependencies, because the pip
# version is linked against the wrong version of libpcl.
#
# $PIP_INSTALL python-pcl

# These packages used to be installed with PIP, presumably because they depend
# on NumPy, but it seems that they do not depend on a particular ABI version.
#
# $PIP_INSTALL -U 'nibabel<2.5'
# $PIP_INSTALL 'dicom'  # pydicom 0.9 API


# IPython/Jupyter: only a very specific combination of versions works correctly
# for our purposes:
# 1. qtconsole in BrainVISA and Anatomist;
# 2. notebook-based tests (e.g. pyaims-tests).
#
# The versions below were tested successfully (the APT versions supplied by
# Ubuntu 18.04 DO NOT work).
$PIP_INSTALL -U 'ipython~=5.9.0' 'ipykernel~=4.10.1' 'tornado~=4.5.3' \
                 'jupyter~=1.0.0' 'jupyter_client~=5.3.4' \
                 'pyzmq~=18.0.2' 'qtconsole~=4.4.4' 'nbconvert==5.6.1' \
                 'ipywidgets' 'ipycanvas' 'ipyevents'

$PIP_INSTALL 'nbsphinx~=0.4.3'
$PIP_INSTALL 'sphinx-gallery~=0.3.1'
$PIP_INSTALL -U 'pygments<3'
$PIP_INSTALL 'jsonschema~=3.2.0' 'attrs~=20.3.0'
$PIP_INSTALL plotly
$PIP_INSTALL sphinx_rtd_theme

# post-install: register jupyter extensions
$SUDO jupyter nbextension enable --py widgetsnbextension
$SUDO jupyter nbextension enable --py ipyevents
$SUDO jupyter nbextension enable --py ipycanvas

# useful tool: pip search has stopped working, but pip_search works
$PIP_INSTALL pip-search
