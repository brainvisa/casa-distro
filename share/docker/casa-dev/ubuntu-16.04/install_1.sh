# Install system dependencies for image cati/casa-dev:ubuntu-16.04

set -e # stop the script on error

set -x # display command before running them
if [ `id -u` -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

. /casa/environment.sh

# add neurodebian repositories and install a few packages
$SUDO wget -O- http://neuro.debian.net/lists/xenial.de-m.full | $SUDO tee /etc/apt/sources.list.d/neurodebian.sources.list
$SUDO apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9

# WARNING: it is necessary to call apt-get install for each package to
# avoid the 101th package issue
$SUDO apt-get update
$SUDO apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y build-essential
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y cmake
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y cmake-curses-gui
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y subversion
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y git
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-dev-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-designer
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-qmake
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-qmlviewer
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-qtconfig
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-linguist-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sip-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-qt4-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsigc++-2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y zlib1g-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y sqlite3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsqlite3-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnetcdf-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libreadline-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libblitz0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtiff-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjpeg-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpng-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmng-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y graphviz
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y graphviz-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libminc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdcmtk2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqwt5-qt4-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y doxygen
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyro
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-paramiko
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxml2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gfortran
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsvm-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-epydoc
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-matplotlib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-qt4-gl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sphinx
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sqlalchemy
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openjdk-8-jdk
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libltdl7-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libncurses5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y vim
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y nano
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y wget
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgtk2.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgtk2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenjpeg-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-common
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y automake
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y texlive-fonts-recommended
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-dicom
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-traits
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y lftp
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y apt-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y g++-4.9
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgfortran-4.9-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqtwebkit-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libblas-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liblapack-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libffi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmpich-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgstreamer1.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgstreamer-plugins-base0.10-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgstreamer-plugins-base1.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liborc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxslt-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libicu-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gdb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mesa-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y x11proto-gl-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-setuptools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y kdesdk-scripts
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y net-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liblapack-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libatlas-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libbz2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libzmq-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgsl0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjasper-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y locate
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libaudio-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-yaml
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pandoc
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gadfly
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtmultimedia
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtopengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtsvg
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtwebkit
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtsql
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtwebsockets
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtxmlpatterns
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-mysqldb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-requests
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-jenkins
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y ipython3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y ipython3-notebook
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y ipython3-qtconsole
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-matplotlib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtmultimedia
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtopengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtsvg
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtwebkit
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtsql
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtwebsockets
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtxmlpatterns
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-traits
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pip
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pydot
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-configobj
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sip-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt4.qtsql
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt4.phonon
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt4.qtopengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sphinx
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sphinx-paramlinks
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pandas
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-xmltodict
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-xmltodict
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-fastcluster
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-mysqldb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sqlalchemy
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyqt5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyqt5-dev-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5opengl5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5svg5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5webkit5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5websockets5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5x11extras5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5xmlpatterns5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5waylandclient5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libphonon4qt5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqwt-qt5-6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qttools5-dev-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qtmultimedia5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtx11extras
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-ipython-genutils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y cython3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-yaml
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-requests
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-jenkins
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnifti-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y x11proto-print-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y bash-completion
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qtpositioning5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5sensors5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdouble-conversion-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgraphite2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libharfbuzz-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhyphen-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-subprocess32
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-keysyms1-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-randr0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-render-util0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-render0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-shape0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-shm0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-sync-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-util-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-xfixes0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-xkb-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-image0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-icccm4-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-render-util0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-dbg
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y wkhtmltopdf
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-joblib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-tqdm
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-joblib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-tqdm
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-dev
$SUDO apt-get clean
$SUDO rm -rf /var/lib/apt/lists/*

# pip3 modules should be installed first, then some commands
# (/usr/local/bin/jupyter* for instance) will be replaced by python2
# equivalents when installed by pip2. jupyter modules especially handle
# these conflicts very badly.
$SUDO pip3 install -U numpy
$SUDO pip3 install -U scipy
$SUDO pip3 install nipype
$SUDO pip3 install jupyter
$SUDO pip3 install nbsphinx
$SUDO pip3 install cython
$SUDO pip3 install dipy
$SUDO pip3 install -U nibabel
$SUDO pip3 install sklearn
$SUDO pip3 install -U 'ipython>=5.0,<6.0'
$SUDO pip3 install -U pandas
$SUDO pip3 install -U lark-parser

# WARNING: easy_install gets installed in /usr/local/bin/easy_install
# for python 3! Same for pip, we have to force installing pip for python2
# using the system easy_install (python2)
$SUDO /usr/bin/easy_install pip

# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
$SUDO pip install -U pkgconfig
$SUDO pip install -U cython
$SUDO pip install -U numpy
$SUDO pip install -U setuptools
CPPFLAGS='-I/usr/include/mpi' $SUDO pip install --no-binary=h5py h5py

# ipython / jupyter
$SUDO pip install -U 'ipython>=5.0,<6.0'
$SUDO pip install jupyter
$SUDO pip install -U zmq
$SUDO pip install -U scipy
$SUDO pip install -U nbsphinx
# sphinx 1.7 has bugs
$SUDO pip install -U "sphinx>=1.5,<1.7"

$SUDO pip install nipype
$SUDO pip install dipy
$SUDO pip install -U nibabel
$SUDO pip install sklearn
$SUDO pip install -U pyparsing
$SUDO pip install -U pydot
$SUDO pip install -U pandas
$SUDO pip install -U lark-parser
