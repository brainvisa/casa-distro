#! /bin/sh
# Install system dependencies for image casa-dev-5.0
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

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

SUDO="sudo"
PIP3="sudo python3 -m pip --no-cache-dir"
$PIP3 install -U pip

# APT only ships six 1.11.0 under Ubuntu 18.04
$PIP3 install 'six~=1.13'

# Python 3 packages that do not exist as APT packages
$PIP3 install 'dipy<0.15'
$PIP3 install 'nipype<1.2'

# Runtime dependencies of populse-db
$PIP3 install 'lark-parser>=0.7,<0.8'

# Runtime dependencies of Morphologist
$PIP3 install 'torch'
$PIP3 install 'torch-vision'

# Runtime dependency of datamind and Constellation
$PIP3 install http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.59.tar.gz

# Development tools are most useful if installed in a recent version by pip,
# even if they are available as APT packages
$PIP3 install modernize  # can be removed when all Python2-only code is gone
$PIP3 install --ignore-installed PyYAML pre-commit
$PIP3 install tox

# These packages used to be installed with PIP instead of APT for an unknown
# reason (maybe this was a careless copy/paste from the Ubuntu 16.04 script).
#
# $PIP3 install -U 'pkgconfig<1.6'
# $PIP3 install -U 'cython<0.30'
# $PIP3 install -U 'xlrd<1.3'
# $PIP3 install -U 'xlwt<1.4'

# Under Ubuntu 18.04 APT supplies numpy 1.13.3 and scipy 0.19.1, which are
# apparently too old for our friends of the MeCA group in Marseille.
# Unfortunately installing the newer NumPy installed with pip is
# ABI-incompatible with the system NumPy (ABI version 9 vs ABI version 8), so
# we need to also install every package that depends on NumPy with pip.
$PIP3 install 'numpy~=1.16,<1.17'
$PIP3 install fastcluster
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
sudo CPPFLAGS='-I/usr/include/mpi' python3 -m pip --no-cache-dir install --no-binary=h5py 'h5py<2.10'
$PIP3 install matplotlib
$PIP3 install 'scipy~=1.2,<1.3'
$PIP3 install scikit-image
$PIP3 install 'scikit-learn<0.21'

# python-pcl is installed in install_compiled_dependencies, because the pip
# version is linked against the wrong version of libpcl.
#
# $PIP3 install python-pcl

# These packages used to be installed with PIP, presumably because they depend
# on NumPy, but it seems that they do not depend on a particular ABI version.
#
# $PIP3 install -U 'nibabel<2.5'
# $PIP3 install 'dicom'  # pydicom 0.9 API


# IPython/Jupyter: only a very specific combination of versions works correctly
# for our purposes:
# 1. qtconsole in BrainVISA and Anatomist;
# 2. notebook-based tests (e.g. pyaims-tests).
#
# The versions below were tested successfully (the APT versions supplied by
# Ubuntu 18.04 DO NOT work).
$PIP3 install -U 'ipython~=5.9.0' 'ipykernel~=4.10.1' 'tornado~=4.5.3' \
                 'jupyter~=1.0.0' 'jupyter_client~=5.3.4' \
                 'pyzmq~=18.0.2' 'qtconsole~=4.4.4' 'nbconvert==5.6.1' \
                 'ipywidgets' 'ipycanvas' 'ipyevents'

$PIP3 install 'nbsphinx~=0.4.3'
$PIP3 install 'sphinx-gallery~=0.3.1'
$PIP3 install -U 'pygments<3'
$PIP3 install 'jsonschema~=3.2.0' 'attrs~=20.3.0'
$PIP3 install plotly
$PIP3 install sphinx_rtd_theme

# post-install: register jupyter extensions
$SUDO jupyter nbextension enable --py widgetsnbextension
$SUDO jupyter nbextension enable --py ipyevents
$SUDO jupyter nbextension enable --py ipycanvas


# Re-install Python 2 packages whose binaries have been overwritten by
# Python 3 versions (/usr/local/bin/jupyter* for instance). jupyter modules
# especially handle these conflicts very badly.
#
# Such modules can be found with 'grep python3 /usr/local/bin/*'
PIP2="sudo python2 -m pip --no-cache-dir"

# Re-install these pip-installed modules to restore the Python 2 binaries. We
# use a sequence of 'pip uninstall', 'pip install' rather than 'pip
# --force-reinstall', because the latter also uninstalls and reinstalls all
# dependencies of the specified packages.
$PIP2 install -U --force-reinstall pip
$PIP2 uninstall --yes jupyter-console
$PIP2 uninstall --yes dipy
$PIP2 install -U --force-reinstall 'ipython~=5.9.0'
$PIP2 install jupyter-console
$PIP2 install 'dipy<0.15'
$PIP2 install sphinx_rtd_theme

# fix pip uglinesses, it did actually wipe away
# /usr/lib/python2.7/dist-packages/backports !
sudo apt-get update
sudo apt-get install --reinstall python-backports.functools-lru-cache python-backports-shutil-get-terminal-size python-configparser
# Free disk space by removing APT caches
sudo apt-get clean
if [ -z "$APT_NO_LIST_CLEANUP" ]; then
    # delete all the apt list files since they're big and get stale quickly
    sudo rm -rf /var/lib/apt/lists/*
fi

# Remove these programs, which hide the Python 2 versions installed by APT.
sudo rm -f /usr/local/bin/nib-*
sudo rm -f /usr/local/bin/nipypecli
