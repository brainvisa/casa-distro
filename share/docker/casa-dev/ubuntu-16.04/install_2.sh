# Install system dependencies for image cati/casa-dev:ubuntu-16.04

set -e # stop the script on error

set -x # display command before running them
if [ `id -u` -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

. /casa/environment.sh

# pip3 modules should be installed first, then some commands
# (/usr/local/bin/jupyter* for instance) will be replaced by python2
# equivalents when installed by pip2. jupyter modules especially handle
# these conflicts very badly.
#
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
$SUDO pip3 install -U pkgconfig
$SUDO pip3 install -U cython
$SUDO pip3 install -U 'numpy==1.16.2'
$SUDO pip3 install -U setuptools
CPPFLAGS='-I/usr/include/mpi' $SUDO pip3 install --no-binary=h5py h5py

$SUDO pip3 install -U 'scipy==1.2.1'
$SUDO pip3 install nipype
$SUDO pip3 install jupyter
$SUDO pip3 install nbsphinx
$SUDO pip3 install cython
$SUDO pip3 install dipy
$SUDO pip3 install -U nibabel
$SUDO pip3 install sklearn
$SUDO pip3 install --ignore-installed -U 'ipython>=5.0,<6.0'
$SUDO pip3 install -U 'pandas==0.24.2'
$SUDO pip3 install -U lark-parser
$SUDO pip3 install -U xlrd
$SUDO pip3 install -U xlwt

# remove python-pip since it can cause conflicts with upgraded versions:
# strangely, /usr/lib/python2.7/dist-packages is *before*
# /usr/local/lib/python2.7/dist-packages in sys.path !
$SUDO apt-get remove -y python-pip
# WARNING: easy_install gets installed in /usr/local/bin/easy_install
# for python 3! Same for pip, we have to force installing pip for python2
# using the system easy_install (python2)
$SUDO /usr/bin/easy_install pip

# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
$SUDO pip install -U pkgconfig
$SUDO pip install -U cython
$SUDO pip install -U 'numpy==1.16.2'
$SUDO pip install -U setuptools
$SUDO pip install -U pip
$SUDO hash pip
CPPFLAGS='-I/usr/include/mpi' $SUDO pip install --no-binary=h5py h5py

# ipython / jupyter
$SUDO pip install --ignore-installed -U 'ipython>=5.0,<6.0'
$SUDO pip install 'ipython<6'
$SUDO pip install 'ipykernel<5'
$SUDO pip install --ignore-installed -U pyzmq
$SUDO pip install jupyter
$SUDO pip install -U zmq
$SUDO pip install --ignore-installed -U 'scipy==1.2.1'
$SUDO pip install -U nbsphinx
# sphinx 1.7 has bugs
$SUDO pip install -U "sphinx>=1.5,<1.7"

$SUDO pip install -U pyparsing
$SUDO pip install nipype
$SUDO pip install dipy
$SUDO pip install -U nibabel
$SUDO pip install sklearn
$SUDO pip install -U pydot
$SUDO pip install -U 'pandas==0.24.2'
$SUDO pip install -U lark-parser
$SUDO pip install --ignore-installed -U xlrd
$SUDO pip install --ignore-installed -U xlwt
