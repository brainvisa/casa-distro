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

# General note: some packages are prevented from being upgraded by appending
# the '<x.y.z' version requirement. Unless noted otherwise, this is done solely
# to prevent accidental breakage during image rebuilds, when new PyPI versions
# introduce incompatible changes. These version blocks should be revised
# regularly!

PIP2="sudo python2 -m pip --no-cache-dir"
$PIP2 install -U pip

# APT only ships six 1.11.0 under Ubuntu 18.04
$PIP2 install 'six~=1.13'

# Runtime dependencies of populse-db
$PIP2 install 'lark-parser>=0.7,<0.8'

# Runtime dependencies of Morphologist
$PIP2 install 'torch'
$PIP2 install 'torch-vision'

# Runtime dependency of datamind and Constellation
$PIP2 install http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.59.tar.gz

# Necessary to fix installation error of h5py
$PIP2 install -U 'pkgconfig<1.6'

# Under Ubuntu 18.04 APT supplies numpy 1.13.3 and scipy 0.19.1, which are
# apparently too old for our friends of the MeCA group in Marseille.
# Unfortunately installing the newer NumPy installed with pip is
# ABI-incompatible with the system NumPy (ABI version 9 vs ABI version 8), so
# we need to also install every package that depends on NumPy with pip.
$PIP2 install -U 'numpy~=1.16,<1.17'
$PIP2 install 'dipy<0.15'
$PIP2 install fastcluster
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
sudo CPPFLAGS='-I/usr/include/mpi' python2 -m pip --no-cache-dir install --no-binary=h5py 'h5py<2.10'
$PIP2 install matplotlib
$PIP2 install -U 'scipy~=1.2,<1.3'
$PIP2 install scikit-image
$PIP2 install 'scikit-learn<0.21'

# These packages used to be installed with PIP, presumably because they depend
# on NumPy, but it seems that they do not depend on a particular ABI version.
#
# $PIP2 install 'nipype<1.2'
# $PIP2 install -U 'nibabel<2.5'
# $PIP2 install -U 'pyparsing<2.4'
# $PIP2 install -U 'pydot<1.3'
# $PIP2 install 'dicom'  # pydicom 0.9 API

# python-pcl is installed in install_compiled_dependencies, because the pip
# version is linked against the wrong version of libpcl.
#
# $PIP2 install python-pcl

# IPython/Jupyter: only a very specific combination of versions works correctly
# for our purposes:
# 1. qtconsole in BrainVISA and Anatomist;
# 2. notebook-based tests (e.g. pyaims-tests).
#
# The versions below were tested successfully (the APT versions supplied by
# Ubuntu 18.04 DO NOT work).
$PIP2 install -U 'ipython~=5.9.0' 'ipykernel~=4.10.1' 'tornado~=4.5.3' \
                 'jupyter~=1.0.0' 'jupyter_client~=5.3.4' \
                 'pyzmq~=18.0.2' 'qtconsole~=4.4.4'

# sphinx 1.7 has bugs
$PIP2 install -U 'sphinx~=1.6.7'
$PIP2 install 'nbsphinx~=0.4.3'
$PIP2 install 'sphinx-gallery~=0.3.1'
$PIP2 install 'jsonschema~=3.2.0' 'attrs~=20.3.0'


# Fix up the matplotlib configuration (the default backend, TkAgg, does not
# work because the python-tk package is not installed in our images).
# Unfortunately matplotlib does not look for a global matplotlibrc in /etc, so
# we have to edit the file in /usr/local in place.
sed -i -e 's/^\s*backend\s*:\s*TkAgg\s*$/backend      : Qt5Agg/' \
    /usr/local/lib/python2.7/dist-packages/matplotlib/mpl-data/matplotlibrc
