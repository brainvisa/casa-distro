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
$SUDO pip3 install -U 'pkgconfig<1.6'
$SUDO pip3 install -U 'cython<0.30'
$SUDO pip3 install -U 'six>=1.12'
$SUDO pip3 install -U 'numpy<1.17'
$SUDO pip3 install -U 'setuptools==40.8.0'
$SUDO pip3 install -U 'pip<19.1'
$SUDO hash pip3
CPPFLAGS='-I/usr/include/mpi' $SUDO pip3 install --no-binary=h5py 'h5py<2.9'

$SUDO pip3 install --ignore-installed -U 'scipy<1.3'
$SUDO pip3 install 'nipype<1.2'
$SUDO pip3 install --ignore-installed -U 'pyzmq<18'
$SUDO pip3 install --ignore-installed -U 'ipython<8'
$SUDO pip3 install 'jupyter==1.0.0'
$SUDO pip3 install --ignore-installed -U 'ipykernel<5' 'tornado<4.5'
$SUDO pip3 install 'nbsphinx<0.4'
# sphinx 1.7 has bugs
$SUDO pip3 install -U "sphinx<1.7"
$SUDO pip3 install 'sphinx-gallery<0.4'
$SUDO pip3 install 'dipy<0.15'
$SUDO pip3 install -U 'nibabel<2.4'
$SUDO pip3 install 'scikit-learn<0.21'
$SUDO pip3 install -U 'pandas<0.25'
$SUDO pip3 install -U 'lark-parser>=0.7,<0.8'
$SUDO pip3 install -U 'xlrd<1.3'
$SUDO pip3 install -U 'xlwt<1.4'
$SUDO pip3 install -U 'openpyxl<3.0'
$SUDO pip3 install torch
$SUDO pip3 install torch-vision
$SUDO pip3 install python-pcl
$SUDO pip3 install fastcluster
$SUDO pip3 install modernize
$SUDO pip3 install pre-commit
$SUDO pip3 install tox
$SUDO pip3 install scikit-image

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
$SUDO pip install -U 'pkgconfig<1.6'
$SUDO pip install -U 'cython<0.30'
$SUDO pip install -U 'six>=1.12'
$SUDO pip install -U 'numpy<1.16'
$SUDO pip install -U 'setuptools==40.8.0'
$SUDO pip install -U 'pip<19.1'
$SUDO hash pip
CPPFLAGS='-I/usr/include/mpi' $SUDO pip install --no-binary=h5py 'h5py<2.9'

# ipython / jupyter
$SUDO pip install --ignore-installed -U 'ipython<6.0'
$SUDO pip install 'ipython<6'
$SUDO pip install 'ipykernel<5'
$SUDO pip install --ignore-installed -U 'pyzmq<18.1'
$SUDO pip install 'jupyter==1.0.0'
$SUDO pip install -U --no-deps --ignore-installed 'scipy<1.2'
$SUDO pip install -U 'nbsphinx<0.4'
# sphinx 1.7 has bugs
$SUDO pip install -U "sphinx<1.7"
$SUDO pip install 'sphinx-gallery<0.4'

$SUDO pip install -U 'pyparsing<2.4'
$SUDO pip install 'nipype<1.2'
$SUDO pip install 'dipy<0.15'
$SUDO pip install -U 'nibabel<2.4'
$SUDO pip install 'scikit-learn<0.21'
$SUDO pip install -U 'pydot<1.4'
$SUDO pip install -U 'pandas<0.25'
$SUDO pip install -U 'lark-parser>=0.7,<0.8'
$SUDO pip install --ignore-installed -U 'xlrd<1.3'
$SUDO pip install --ignore-installed -U 'xlwt<1.4'

$SUDO pip install torch
$SUDO pip install torch-vision
$SUDO pip install python-pcl
$SUDO pip install fastcluster
