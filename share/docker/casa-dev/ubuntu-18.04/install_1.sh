# Install system dependencies for image cati/casa-dev:ubuntu-18.04
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them

if [ $(id -u) -eq 0 ]; then
    SUDO=
    APT_GET=apt-get
else
    SUDO=sudo
    APT_GET="sudo apt-get"
fi


###############################################################################
# Install system packages with apt-get
###############################################################################

export DEBIAN_FRONTEND=noninteractive
APT_GET_INSTALL="$APT_GET install --no-install-recommends -y"

# install python and pip to get apt-mirror-updater
# in order to select an efficient debian mirror.
# (try installing up to 5 times if the default server sometimes disconnects)
for trial in 1 2 3 4 5; do
    $APT_GET update && break
done
for trial in 1 2 3 4 5; do
    $APT_GET_INSTALL python-pip && break
done
$SUDO pip install apt-mirror-updater
# setup best mirror in /etc/apt/sources.list
$SUDO apt-mirror-updater -a

# Add neurodebian repositories (TODO: remove once this image is based on casa-run)
$APT_GET_INSTALL gnupg  # needed by apt-key (below)
$SUDO wget -O /etc/apt/sources.list.d/neurodebian.sources.list http://neuro.debian.net/lists/bionic.de-m.full
$SUDO apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9

$APT_GET update

# WARNING: it is necessary to call apt-get install separately for small groups
# of packages to avoid the mysterious 101st package issue (Download of the
# 101st package fails randomly in NeuroSpin, maybe due to firewall issues).
#
# TODO: as indirect dependencies were removed from this list, it may be that
# some lines trigger the installation of more than 100 packages. If this is the
# case, we have to re-introduce indirect dependencies here, but this time we
# will *explicitly* mark them as such, to avoid ever having to disentangle this
# mess again...

# Probably obsolete packages (TODO: remove)
# $APT_GET_INSTALL apt-utils
# $APT_GET_INSTALL gadfly  # obsolete dep? (only used in datamind)
# $APT_GET_INSTALL libgsl-dev  # was used in highres-cortex (only?)
# $APT_GET_INSTALL openjdk-8-jdk  # was used for Docbook docs
# $APT_GET_INSTALL pyro  # obsolete since soma-workflow 3

# Dubious packages (TODO: check why they were added / if they are really needed)
# $APT_GET_INSTALL gdal-data
# $APT_GET_INSTALL i965-va-driver
# $APT_GET_INSTALL ibverbs-providers
# $APT_GET_INSTALL libbdplus0
# $APT_GET_INSTALL libbluray2
# $APT_GET_INSTALL libavcodec57
# $APT_GET_INSTALL libavformat57
# $APT_GET_INSTALL libchromaprint1
# $APT_GET_INSTALL libcrystalhd3
# $APT_GET_INSTALL libgme0
# $APT_GET_INSTALL libgsm1
# $APT_GET_INSTALL libmp3lame0
# $APT_GET_INSTALL libmpg123-0
# $APT_GET_INSTALL libnl-route-3-200
# $APT_GET_INSTALL libopenmpt0
# $APT_GET_INSTALL software-properties-common

# Runtime dependencies (TODO: remove once this image is based on casa-run)
$APT_GET_INSTALL lftp
$APT_GET_INSTALL libopenblas-base
$APT_GET_INSTALL libatlas3-base
$APT_GET_INSTALL libqwt-qt5-6
$APT_GET_INSTALL mesa-utils
$APT_GET_INSTALL net-tools  # really useful?
$APT_GET_INSTALL python-setuptools  # needed to install source packages from pip
$APT_GET_INSTALL sqlite3
$APT_GET_INSTALL unzip
$APT_GET_INSTALL libaacs0
$APT_GET_INSTALL libarmadillo8
$APT_GET_INSTALL libarpack2
$APT_GET_INSTALL libdap25
$APT_GET_INSTALL libdapclient6v5
$APT_GET_INSTALL libdapserver7v5
$APT_GET_INSTALL libepsilon1
$APT_GET_INSTALL libflann1.9
$APT_GET_INSTALL libfreexl1
$APT_GET_INSTALL mpi-default-bin

# Seemingly redundant packages (TODO: check and remove)
$APT_GET_INSTALL libgtk2.0  # does not exist??
$APT_GET_INSTALL libgdk-pixbuf2.0-0
$APT_GET_INSTALL libgdk-pixbuf2.0-dev

# Source version control
$APT_GET_INSTALL kdesdk-scripts  # for the colorsvn script
$APT_GET_INSTALL git
$APT_GET_INSTALL git-lfs
$APT_GET_INSTALL subversion

# Configure/build toolchain
$APT_GET_INSTALL automake
$APT_GET_INSTALL build-essential
$APT_GET_INSTALL clang
$APT_GET_INSTALL cmake
$APT_GET_INSTALL cmake-curses-gui
$APT_GET_INSTALL gfortran
$APT_GET_INSTALL python-sip-dev
$APT_GET_INSTALL python3-sip-dev

# Development tools and convenience utilities
$APT_GET_INSTALL bash-completion
$APT_GET_INSTALL flake8
$APT_GET_INSTALL gdb
$APT_GET_INSTALL gedit
$APT_GET_INSTALL gitg
$APT_GET_INSTALL gitk
$APT_GET_INSTALL kate
$APT_GET_INSTALL kdiff3
$APT_GET_INSTALL kompare
$APT_GET_INSTALL kwrite
$APT_GET_INSTALL locate
$APT_GET_INSTALL meld
$APT_GET_INSTALL nano
$APT_GET_INSTALL python-autopep8
$APT_GET_INSTALL python-dbg
$APT_GET_INSTALL spyder
$APT_GET_INSTALL vim
$APT_GET_INSTALL xterm

# Documentation building
$APT_GET_INSTALL doxygen
$APT_GET_INSTALL ghostscript
$APT_GET_INSTALL graphviz
$APT_GET_INSTALL graphviz-dev
$APT_GET_INSTALL pandoc
$APT_GET_INSTALL python-epydoc
$APT_GET_INSTALL python-sphinx
$APT_GET_INSTALL texlive-fonts-recommended
$APT_GET_INSTALL wkhtmltopdf

# Framework-specific tools
$APT_GET_INSTALL pyqt5-dev
$APT_GET_INSTALL pyqt5-dev-tools
$APT_GET_INSTALL qt5-default
$APT_GET_INSTALL qttools5-dev-tools
$APT_GET_INSTALL qttools5-private-dev


# Python 2 packages (TODO: to be moved to casa-run)
$APT_GET_INSTALL python-paramiko
$APT_GET_INSTALL python-matplotlib
$APT_GET_INSTALL python-dicom
$APT_GET_INSTALL python-traits
$APT_GET_INSTALL python-yaml
$APT_GET_INSTALL python-pyqt5
$APT_GET_INSTALL python-pyqt5.qtmultimedia
$APT_GET_INSTALL python-pyqt5.qtopengl
$APT_GET_INSTALL python-pyqt5.qtsvg
$APT_GET_INSTALL python-pyqt5.qtwebkit
$APT_GET_INSTALL python-pyqt5.qtsql
$APT_GET_INSTALL python-pyqt5.qtwebsockets
$APT_GET_INSTALL python-pyqt5.qtxmlpatterns
$APT_GET_INSTALL python-mysqldb
$APT_GET_INSTALL python-requests
$APT_GET_INSTALL python-sqlalchemy
$APT_GET_INSTALL python-xmltodict
## TODO(ylep): here
$APT_GET_INSTALL python-opengl
$APT_GET_INSTALL python-joblib
$APT_GET_INSTALL python-tqdm
$APT_GET_INSTALL python-autobahn
$APT_GET_INSTALL python-automat
$APT_GET_INSTALL python-cbor
$APT_GET_INSTALL python-click
$APT_GET_INSTALL python-colorama
$APT_GET_INSTALL python-concurrent.futures
$APT_GET_INSTALL python-constantly
$APT_GET_INSTALL python-hyperlink
$APT_GET_INSTALL python-incremental
$APT_GET_INSTALL python-mpi4py
$APT_GET_INSTALL python-nacl
$APT_GET_INSTALL python-pam
$APT_GET_INSTALL python-pyasn1-modules
$APT_GET_INSTALL python-qrcode
$APT_GET_INSTALL python-serial
$APT_GET_INSTALL python-service-identity
$APT_GET_INSTALL python-snappy
$APT_GET_INSTALL python-trie
$APT_GET_INSTALL python-trollius
$APT_GET_INSTALL python-twisted
$APT_GET_INSTALL python-twisted-bin
$APT_GET_INSTALL python-twisted-core
$APT_GET_INSTALL python-txaio
$APT_GET_INSTALL python-u-msgpack
$APT_GET_INSTALL python-ubjson
$APT_GET_INSTALL python-vtk6
$APT_GET_INSTALL python-wsaccel
$APT_GET_INSTALL python-zope.interface

# Python 3 packages
$APT_GET_INSTALL python3-matplotlib
$APT_GET_INSTALL python3-pyqt5
$APT_GET_INSTALL python3-pyqt5.qtmultimedia
$APT_GET_INSTALL python3-pyqt5.qtopengl
$APT_GET_INSTALL python3-pyqt5.qtsvg
$APT_GET_INSTALL python3-pyqt5.qtwebkit
$APT_GET_INSTALL python3-pyqt5.qtsql
$APT_GET_INSTALL python3-pyqt5.qtwebsockets
$APT_GET_INSTALL python3-pyqt5.qtxmlpatterns
$APT_GET_INSTALL python3-traits
$APT_GET_INSTALL python3-pip
$APT_GET_INSTALL python3-pydot
$APT_GET_INSTALL python3-configobj
$APT_GET_INSTALL python3-sphinx
$APT_GET_INSTALL python3-sphinx-paramlinks
$APT_GET_INSTALL python3-pandas
$APT_GET_INSTALL python3-xmltodict
$APT_GET_INSTALL python3-fastcluster
$APT_GET_INSTALL python3-sqlalchemy
$APT_GET_INSTALL python3-mysqldb
$APT_GET_INSTALL python3-pyqt5.qtx11extras
$APT_GET_INSTALL python3-ipython-genutils
$APT_GET_INSTALL python3-yaml
$APT_GET_INSTALL python3-requests
$APT_GET_INSTALL python3-jenkins
$APT_GET_INSTALL python3-opengl
$APT_GET_INSTALL python3-joblib
$APT_GET_INSTALL python3-tqdm
$APT_GET_INSTALL python3-dicom

# Development packages of compiled libraries (C/C++/Fortran)
# TODO: clean up this list of its indirect dependencies
$APT_GET_INSTALL libsigc++-2.0-dev
$APT_GET_INSTALL zlib1g-dev
$APT_GET_INSTALL libsqlite3-dev
$APT_GET_INSTALL libnetcdf-dev
$APT_GET_INSTALL libreadline-dev
$APT_GET_INSTALL libboost-dev
$APT_GET_INSTALL libtiff-dev
$APT_GET_INSTALL libjpeg-dev
$APT_GET_INSTALL libpng-dev
$APT_GET_INSTALL libmng-dev
$APT_GET_INSTALL libminc-dev
$APT_GET_INSTALL libdcmtk-dev
$APT_GET_INSTALL libxml2-dev
$APT_GET_INSTALL libsvm-dev
$APT_GET_INSTALL libltdl7-dev
$APT_GET_INSTALL libncurses5-dev
$APT_GET_INSTALL libgtk2.0-dev
$APT_GET_INSTALL libjpeg-turbo8-dev
$APT_GET_INSTALL libblas-dev
$APT_GET_INSTALL liblapack-dev
$APT_GET_INSTALL libffi-dev
$APT_GET_INSTALL libmpich-dev
$APT_GET_INSTALL libgstreamer1.0-dev
$APT_GET_INSTALL libgstreamer-plugins-base1.0-dev
$APT_GET_INSTALL liborc-0.4-dev
$APT_GET_INSTALL libxslt1-dev
$APT_GET_INSTALL libicu-dev
$APT_GET_INSTALL x11proto-gl-dev
$APT_GET_INSTALL libbz2-dev
$APT_GET_INSTALL libzmq3-dev
$APT_GET_INSTALL libaudio-dev
$APT_GET_INSTALL libqt5opengl5-dev
$APT_GET_INSTALL libqt5svg5-dev
$APT_GET_INSTALL libqt5webkit5-dev
$APT_GET_INSTALL libqt5websockets5-dev
$APT_GET_INSTALL libqt5x11extras5-dev
$APT_GET_INSTALL libqt5xmlpatterns5-dev
$APT_GET_INSTALL libqt5waylandclient5-dev
$APT_GET_INSTALL libqt5webenginewidgets5
$APT_GET_INSTALL libqt5webview5-dev
$APT_GET_INSTALL qtwebengine5-dev
$APT_GET_INSTALL libphonon4qt5-dev
$APT_GET_INSTALL qttools5-dev
$APT_GET_INSTALL qtmultimedia5-dev
$APT_GET_INSTALL libnifti-dev
$APT_GET_INSTALL x11proto-print-dev
$APT_GET_INSTALL libopenjp2-7-dev
$APT_GET_INSTALL libqwt-qt5-dev
$APT_GET_INSTALL qtpositioning5-dev
$APT_GET_INSTALL libqt5sensors5-dev
$APT_GET_INSTALL libqt5webchannel5-dev
$APT_GET_INSTALL libdouble-conversion-dev
$APT_GET_INSTALL libgraphite2-dev
$APT_GET_INSTALL libharfbuzz-dev
$APT_GET_INSTALL libhyphen-dev
## TODO(ylep): here
$APT_GET_INSTALL libwebp-dev
$APT_GET_INSTALL libwoff-dev
$APT_GET_INSTALL libxcb-keysyms1-dev
$APT_GET_INSTALL libxcb-randr0
$APT_GET_INSTALL libxcb-render-util0
$APT_GET_INSTALL libxcb-render0-dev
$APT_GET_INSTALL libxcb-shape0-dev
$APT_GET_INSTALL libxcb-shm0-dev
$APT_GET_INSTALL libxcb-sync-dev
$APT_GET_INSTALL libxcb-util-dev
$APT_GET_INSTALL libxcb-xfixes0-dev
$APT_GET_INSTALL libxcb-xkb-dev
$APT_GET_INSTALL libxcb-image0-dev
$APT_GET_INSTALL libxcb-icccm4-dev
$APT_GET_INSTALL libxcb-render-util0-dev
$APT_GET_INSTALL libxcb-xinerama0-dev
$APT_GET_INSTALL default-libmysqlclient-dev
$APT_GET_INSTALL libarmadillo-dev
$APT_GET_INSTALL libarpack2-dev
$APT_GET_INSTALL libavcodec-dev
$APT_GET_INSTALL libavutil-dev
$APT_GET_INSTALL libboost-all-dev
$APT_GET_INSTALL libdap-dev
$APT_GET_INSTALL libeigen3-dev
$APT_GET_INSTALL libepsilon-dev
$APT_GET_INSTALL libflann-dev
$APT_GET_INSTALL libfreexl-dev
$APT_GET_INSTALL libfyba-dev
$APT_GET_INSTALL libgdal-dev
$APT_GET_INSTALL libgeos-dev
$APT_GET_INSTALL libgeotiff-dev
$APT_GET_INSTALL libgif-dev
$APT_GET_INSTALL libgl2ps-dev
$APT_GET_INSTALL libavformat-dev
$APT_GET_INSTALL libhdf4-alt-dev
$APT_GET_INSTALL libhdf5-mpi-dev
$APT_GET_INSTALL libhdf5-openmpi-dev
$APT_GET_INSTALL libhwloc-dev
$APT_GET_INSTALL libibverbs-dev
$APT_GET_INSTALL libjson-c-dev
$APT_GET_INSTALL libjsoncpp-dev
$APT_GET_INSTALL libkml-dev
$APT_GET_INSTALL libminizip-dev
$APT_GET_INSTALL libmysqlclient-dev
$APT_GET_INSTALL libnetcdf-cxx-legacy-dev
$APT_GET_INSTALL libnuma-dev
$APT_GET_INSTALL libogdi3.2-dev
$APT_GET_INSTALL libogg-dev
$APT_GET_INSTALL libopenni-dev
$APT_GET_INSTALL libopenni2-dev
$APT_GET_INSTALL libpcl-dev
$APT_GET_INSTALL libpoppler-dev
$APT_GET_INSTALL libpoppler-private-dev
$APT_GET_INSTALL libpq-dev
$APT_GET_INSTALL libproj-dev
$APT_GET_INSTALL libqhull-dev
$APT_GET_INSTALL libspatialite-dev
$APT_GET_INSTALL libsuperlu-dev
$APT_GET_INSTALL libswresample-dev
$APT_GET_INSTALL libswscale-dev
$APT_GET_INSTALL libtheora-dev
$APT_GET_INSTALL liburiparser-dev
$APT_GET_INSTALL libvtk6-dev
$APT_GET_INSTALL libvtk6-qt-dev
$APT_GET_INSTALL libxerces-c-dev
$APT_GET_INSTALL libxss-dev
$APT_GET_INSTALL mpi-default-dev
$APT_GET_INSTALL unixodbc-dev
$APT_GET_INSTALL uuid-dev
$APT_GET_INSTALL x11proto-scrnsaver-dev

$APT_GET clean
# delete all the apt list files since they're big and get stale quickly
$SUDO rm -rf /var/lib/apt/lists/*
