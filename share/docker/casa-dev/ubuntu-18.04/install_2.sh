# Install system dependencies for image cati/casa-dev:ubuntu-18.04
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them

if [ $(id -u) -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi


###############################################################################
# Install Python packages with pip
###############################################################################

cd /tmp
wget --no-check-certificate https://github.com/blitzpp/blitz/archive/1.0.2.tar.gz
tar -zxf 1.0.2.tar.gz
mkdir blitz-1.0.2/build
cd blitz-1.0.2
./configure
make -j4
$SUDO make install
cd ..
rm -rf 1.0.2.tar.gz blitz-1.0.2

# remove a few packages that will be reinstalled via pip as newer versions
$SUDO apt-get remove -y python3-scipy
$SUDO apt-get remove -y python-scipy
$SUDO apt-get remove -y python-zmq

# pip3 modules should be installed first, then some commands
# (/usr/local/bin/jupyter* for instance) will be replaced by python2
# equivalents when installed by pip2. jupyter modules especially handle
# these conflicts very badly.

# WARNING: easy_install gets installed in /usr/local/bin/easy_install
# for python 3! Same for pip, we have to force installing pip for python2
# using the system easy_install (python2)
$SUDO pip3 install -U 'setuptools==40.8.0'
$SUDO pip3 install -U 'pip<19.1'
PIP3=/usr/local/bin/pip3
$SUDO hash pip3
$SUDO $PIP3 install -U 'pkgconfig<1.6'
$SUDO $PIP3 install -U 'cython<0.30'
$SUDO $PIP3 install -U 'numpy<1.17'
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
CPPFLAGS='-I/usr/include/mpi' $SUDO $PIP3 install --no-binary=h5py 'h5py<2.10'

$SUDO $PIP3 install -U 'scipy<1.3'
$SUDO $PIP3 install 'nipype<1.2'
$SUDO $PIP3 install 'pyzmq<18'
$SUDO $PIP3 install -U 'ipython<8'
$SUDO $PIP3 install jupyter
$SUDO $PIP3 install --ignore-installed -U 'ipykernel<5' 'tornado<4.5'
$SUDO $PIP3 install 'qtconsole<4.5'
$SUDO $PIP3 install -U 'nbsphinx<0.5'
$SUDO $PIP3 install 'sphinx-gallery<0.4'
$SUDO $PIP3 install 'dipy<0.15'
$SUDO $PIP3 install -U 'nibabel<2.5'
$SUDO $PIP3 install 'scikit-learn<0.21'
$SUDO $PIP3 install -U 'lark-parser>=0.7,<0.8'
$SUDO $PIP3 install -U 'xlrd<1.3'
$SUDO $PIP3 install -U 'xlwt<1.4'
$SUDO $PIP3 install 'torch'
$SUDO $PIP3 install 'torch-vision'
$SUDO $PIP3 install 'dicom'  # pydicom 0.9 API
# $SUDO $PIP3 install python-pcl
$SUDO $PIP3 install fastcluster
$SUDO $PIP3 install modernize
$SUDO $PIP3 install -U -I 'pyyaml<5.4'
$SUDO $PIP3 install pre-commit
$SUDO $PIP3 install tox
$SUDO $PIP3 install scikit-image

# TODO: remove the pip2 installs once this image is based on casa-run

# pip3 upgrade has overwritten pip, we must reinstall it, not using pip exe
$SUDO python -m pip install -U 'setuptools==40.8.0'
$SUDO python -m pip install -U 'pip<19.1'
PIP2=/usr/local/bin/pip2
$SUDO hash pip
$SUDO $PIP2 install -U 'pkgconfig<1.6'
$SUDO $PIP2 install --ignore-installed -U 'cython<0.30'
$SUDO $PIP2 install -U 'numpy<1.17'
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
CPPFLAGS='-I/usr/include/mpi' $SUDO pip2 install --no-binary=h5py 'h5py<2.10'

# ipython / jupyter
$SUDO $PIP2 install -U 'pyzmq<18.1'
$SUDO $PIP2 install -U 'ipython<6.0'
$SUDO $PIP2 install jupyter
$SUDO $PIP2 install jupyter_client
$SUDO $PIP2 install 'qtconsole<4.5'
$SUDO $PIP2 install -U 'scipy<1.3'
$SUDO $PIP2 install -U 'nbsphinx<0.5'
# sphinx 1.7 has bugs
$SUDO $PIP2 install -U "sphinx<1.7"
$SUDO $PIP2 install 'sphinx-gallery<0.4'

$SUDO $PIP2 install 'nipype<1.2'
$SUDO $PIP2 install 'dipy<0.15'
$SUDO $PIP2 install -U 'nibabel<2.5'
$SUDO $PIP2 install 'scikit-learn<0.21'
$SUDO $PIP2 install -U 'pyparsing<2.4'
$SUDO $PIP2 install -U 'pydot<1.3'
$SUDO $PIP2 install "python_jenkins==0.4.16"
$SUDO $PIP2 install -U 'lark-parser>=0.7,<0.8'
$SUDO $PIP2 install -U 'xlrd<1.3'
$SUDO $PIP2 install -U 'xlwt<1.4'
$SUDO $PIP2 install -U 'pandas<0.25'
$SUDO $PIP2 install 'torch'
$SUDO $PIP2 install 'torch-vision'
$SUDO $PIP2 install 'dicom'  # pydicom 0.9 API
# $SUDO $PIP2 install python-pcl  # linked against wrong version of libpcl
$SUDO $PIP2 install fastcluster

# this one needs reinstalling in pip since the whole module backports has
# changed location... pip is a mess, I tell you...
$SUDO $PIP3 install -U backports.functools_lru_cache
$SUDO $PIP2 install -U backports.functools_lru_cache
