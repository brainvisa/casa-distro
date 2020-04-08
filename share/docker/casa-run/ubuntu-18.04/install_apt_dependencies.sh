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

if [ $(id -u) -eq 0 ]; then
    SUDO=
    APT_GET='apt-get -o Acquire::Retries=3'
else
    SUDO=sudo
    APT_GET="sudo apt-get -o Acquire::Retries=3"
fi

###############################################################################
# Install runtime dependencies with apt-get
###############################################################################

export DEBIAN_FRONTEND=noninteractive
APT_GET_INSTALL="$APT_GET install --no-install-recommends -y"

$APT_GET update
$APT_GET_INSTALL gnupg  # needed by apt-key (below)

# These files allow to configure the NeuroDebian repository in a similar way as
# the method described on http://neuro.debian.net/, without requiring insecure
# HTTP connection or network access to the sometimes unreliable keyservers.
#
# If NeuroDebian update their repository or key, we may need to update these
# files. (use 'apt-key export' to write neurodebian-key.gpg).
$SUDO cp /tmp/neurodebian.sources.list \
         /etc/apt/sources.list.d/neurodebian.sources.list
$SUDO apt-key add /tmp/neurodebian-key.gpg

$APT_GET update

# WARNING: it is necessary to call apt-get install separately for small groups
# of packages to avoid the mysterious 101st package issue (Download of the
# 101st package fails randomly in NeuroSpin, maybe due to firewall issues).

# Runtime dependencies of FSL
$APT_GET_INSTALL bc dc libopenblas-base tcsh

# Runtime dependencies of MATLAB
$APT_GET_INSTALL lsb-core libxext6 libxt6 libxmu6

# Generally useful packages
$APT_GET_INSTALL ca-certificates curl file less
$APT_GET_INSTALL lsb-release sudo unzip wget xz-utils

# Dependencies of headless Anatomist
$APT_GET_INSTALL xvfb libx11-xcb1 libfontconfig1 libdbus-1-3 libxrender1
$APT_GET_INSTALL libglib2.0-0 libxi6 x11-utils mesa-utils
cd /tmp
wget https://sourceforge.net/projects/virtualgl/files/2.6.3/virtualgl_2.6.3_amd64.deb
$APT_GET_INSTALL libglu1-mesa  # dependency of virtualgl
$SUDO dpkg -i virtualgl_2.6.3_amd64.deb
rm -f /tmp/virtualgl_2.6.3_amd64.deb

# Runtime components corresponding to libraries installed in
# casa-dev/install_1.sh

# Python packages needed by the installation process
$APT_GET_INSTALL python-pip python-setuptools

# Python packages needed at runtime by BrainVISA
$APT_GET_INSTALL python-dicom
$APT_GET_INSTALL python-matplotlib
$APT_GET_INSTALL python-mysqldb
$APT_GET_INSTALL python-paramiko
$APT_GET_INSTALL python-requests
$APT_GET_INSTALL python-setuptools
# $APT_GET_INSTALL python-six  # Ubuntu 18.04 ships 1.11.0, we need >= 1.13
$APT_GET_INSTALL python-sqlalchemy
$APT_GET_INSTALL python-traits
$APT_GET_INSTALL python-xmltodict
$APT_GET_INSTALL python-yaml
# TODO: the following dependencies used to be installed with pip, check that
# they work when installed with apt
$APT_GET_INSTALL cython
$APT_GET_INSTALL python-numpy
$APT_GET_INSTALL python-zmq
$APT_GET_INSTALL python-ipython
$APT_GET_INSTALL python-jupyter-client
$APT_GET_INSTALL python-qtconsole
$APT_GET_INSTALL python-scipy
$APT_GET_INSTALL python-nbsphinx
$APT_GET_INSTALL python-sphinx-gallery
$APT_GET_INSTALL python-nipype
$APT_GET_INSTALL python-dipy
$APT_GET_INSTALL python-nibabel
$APT_GET_INSTALL python-skimage
$APT_GET_INSTALL python-sklearn
$APT_GET_INSTALL python-pyparsing
$APT_GET_INSTALL python-pydot
$APT_GET_INSTALL python-jenkinsapi
$APT_GET_INSTALL python-pydicom
$APT_GET_INSTALL python-fastcluster
$APT_GET_INSTALL python-backports.functools-lru-cache
# SIP and PyQT are compiled in install_compiled_dependencies.sh to work around
# a bug in the APT version of sip 4.19 concerning virtual C++ inheritance.
#
# $APT_GET_INSTALL python-pyqt5 python-pyqt5.qtmultimedia python-pyqt5.qtopengl python-pyqt5.qtsvg python-pyqt5.qtwebkit python-pyqt5.qtsql python-pyqt5.qtwebsockets python-pyqt5.qtxmlpatterns
# $APT_GET_INSTALL python-sip


# Dynamic libraries needed at runtime by BrainVISA
$APT_GET_INSTALL libpython2.7
$APT_GET_INSTALL libsigc++-2.0-0v5
$APT_GET_INSTALL zlib1g
$APT_GET_INSTALL libreadline7
$APT_GET_INSTALL libtiff5
$APT_GET_INSTALL libtiffxx5
$APT_GET_INSTALL libjpeg8
$APT_GET_INSTALL libpng16-16
$APT_GET_INSTALL libmng2
$APT_GET_INSTALL libminc2-4.0.0
$APT_GET_INSTALL libdcmtk12
$APT_GET_INSTALL libxml2
$APT_GET_INSTALL libsvm3
$APT_GET_INSTALL libltdl7
$APT_GET_INSTALL libncurses5
$APT_GET_INSTALL libjpeg-turbo8
$APT_GET_INSTALL libblas3
$APT_GET_INSTALL libatlas3-base
$APT_GET_INSTALL liblapack3
$APT_GET_INSTALL libffi6
$APT_GET_INSTALL libmpich12
$APT_GET_INSTALL libgstreamer1.0-0
$APT_GET_INSTALL libgstreamer-plugins-base1.0-0
$APT_GET_INSTALL liborc-0.4-0
$APT_GET_INSTALL libxslt1.1
$APT_GET_INSTALL libicu60
$APT_GET_INSTALL libiculx60
$APT_GET_INSTALL libbz2-1.0
$APT_GET_INSTALL libzmq5
$APT_GET_INSTALL libqt5opengl5
$APT_GET_INSTALL libqt5svg5
$APT_GET_INSTALL libqt5webkit5
$APT_GET_INSTALL libqt5websockets5
$APT_GET_INSTALL libqt5x11extras5
$APT_GET_INSTALL libqt5xmlpatterns5
$APT_GET_INSTALL libqt5waylandclient5
$APT_GET_INSTALL libqt5webenginewidgets5
$APT_GET_INSTALL libqt5webview5
$APT_GET_INSTALL libqt5webengine5
$APT_GET_INSTALL libphonon4qt5-4
$APT_GET_INSTALL libqwt-qt5-6
$APT_GET_INSTALL libqt5multimedia5
$APT_GET_INSTALL libnifti2
$APT_GET_INSTALL libopenjp2-7
$APT_GET_INSTALL libqt5positioning5
$APT_GET_INSTALL libqt5sensors5
$APT_GET_INSTALL libqt5webchannel5
$APT_GET_INSTALL libdouble-conversion1
$APT_GET_INSTALL libgraphite2-3
$APT_GET_INSTALL libharfbuzz0b
$APT_GET_INSTALL libhyphen0

## TODO(ylep): after this mark the -dev packages in install_1.sh have not been
## reviewed and their corresponding runtime package added to casa-run

$APT_GET_INSTALL libaacs0
$APT_GET_INSTALL libarmadillo8
$APT_GET_INSTALL libarpack2
$APT_GET_INSTALL libdap25
$APT_GET_INSTALL libdapclient6v5
$APT_GET_INSTALL libdapserver7v5
$APT_GET_INSTALL libepsilon1
$APT_GET_INSTALL libfabric1
$APT_GET_INSTALL libflann1.9
$APT_GET_INSTALL libfreexl1
$APT_GET_INSTALL libfyba0
$APT_GET_INSTALL libgdal20
$APT_GET_INSTALL libgeos-c1v5
$APT_GET_INSTALL libgeotiff2
$APT_GET_INSTALL libgl2ps1.4
$APT_GET_INSTALL libhdf4-0-alt
$APT_GET_INSTALL libhdf5-openmpi-100
$APT_GET_INSTALL libibverbs1
$APT_GET_INSTALL libkmlbase1
$APT_GET_INSTALL libkmlconvenience1
$APT_GET_INSTALL libkmldom1
$APT_GET_INSTALL libkmlengine1
$APT_GET_INSTALL libkmlregionator1
$APT_GET_INSTALL libkmlxsd1
$APT_GET_INSTALL libminizip1
$APT_GET_INSTALL libodbc1
$APT_GET_INSTALL libpcl-apps1.8
$APT_GET_INSTALL libpcl-common1.8
$APT_GET_INSTALL libpcl-features1.8
$APT_GET_INSTALL libpcl-filters1.8
$APT_GET_INSTALL libpcl-io1.8
$APT_GET_INSTALL libpcl-kdtree1.8
$APT_GET_INSTALL libpcl-keypoints1.8
$APT_GET_INSTALL libpcl-ml1.8
$APT_GET_INSTALL libpcl-octree1.8
$APT_GET_INSTALL libpcl-outofcore1.8
$APT_GET_INSTALL libpcl-people1.8
$APT_GET_INSTALL libpcl-recognition1.8
$APT_GET_INSTALL libpcl-registration1.8
$APT_GET_INSTALL libpcl-sample-consensus1.8
$APT_GET_INSTALL libpcl-search1.8
$APT_GET_INSTALL libpcl-segmentation1.8
$APT_GET_INSTALL libpcl-stereo1.8
$APT_GET_INSTALL libpcl-surface1.8
$APT_GET_INSTALL libpcl-tracking1.8
$APT_GET_INSTALL libpcl-visualization1.8
$APT_GET_INSTALL libqhull-r7
$APT_GET_INSTALL libqhull7
$APT_GET_INSTALL libssh-gcrypt-4
$APT_GET_INSTALL liburiparser1
$APT_GET_INSTALL libvtk6.3-qt
$APT_GET_INSTALL libxerces-c3.2
$APT_GET_INSTALL libjxr0  # for openslide (MIRCen fork with CZI support)

# To be sorted
$APT_GET_INSTALL vtk6
$APT_GET_INSTALL xbitmaps

# Other runtime dependencies of BrainVISA
$APT_GET_INSTALL python2.7
$APT_GET_INSTALL lftp
$APT_GET_INSTALL sqlite3


# Dubious packages (TODO: check if they are really needed)
# $APT_GET_INSTALL libbdplus0
# $APT_GET_INSTALL libbluray2
# $APT_GET_INSTALL libavcodec57
# $APT_GET_INSTALL libavformat57
# $APT_GET_INSTALL libavformat-dev
# $APT_GET_INSTALL libavutil55
# $APT_GET_INSTALL libchromaprint1
# $APT_GET_INSTALL libcrystalhd3
# $APT_GET_INSTALL libgme0
# $APT_GET_INSTALL libgsm1
# $APT_GET_INSTALL libmp3lame0
# $APT_GET_INSTALL libmpg123-0
# $APT_GET_INSTALL libnetcdf-c++4
# $APT_GET_INSTALL libnl-route-3-200
# $APT_GET_INSTALL libogdi3.2
# $APT_GET_INSTALL libopenmpt0
# $APT_GET_INSTALL libopenni0
# $APT_GET_INSTALL libopenni2-0
# $APT_GET_INSTALL libopenni-sensor-pointclouds0
# $APT_GET_INSTALL libpq5
# $APT_GET_INSTALL libproj12
# $APT_GET_INSTALL libpsm-infinipath1
# $APT_GET_INSTALL librdmacm1
# $APT_GET_INSTALL libshine3
# $APT_GET_INSTALL libsoxr0
# $APT_GET_INSTALL libspatialite7
# $APT_GET_INSTALL libspeex1
# $APT_GET_INSTALL libsuperlu5
# $APT_GET_INSTALL libswresample2
# $APT_GET_INSTALL libswscale4
# $APT_GET_INSTALL libtwolame0
# $APT_GET_INSTALL libutempter0
# $APT_GET_INSTALL libtinyxml2.6.2v5
# $APT_GET_INSTALL libva-drm2
# $APT_GET_INSTALL libva-x11-2
# $APT_GET_INSTALL libva2
# $APT_GET_INSTALL libvdpau1
# $APT_GET_INSTALL libvorbisfile3
# $APT_GET_INSTALL libvpx5
# $APT_GET_INSTALL libwavpack1
# $APT_GET_INSTALL libx264-152
# $APT_GET_INSTALL libx265-146
# $APT_GET_INSTALL libxvidcore4
# $APT_GET_INSTALL libzvbi-common
# $APT_GET_INSTALL libzvbi0
# $APT_GET_INSTALL mesa-va-drivers
# $APT_GET_INSTALL mesa-vdpau-drivers
# $APT_GET_INSTALL odbcinst
# $APT_GET_INSTALL odbcinst1debian2
# $APT_GET_INSTALL openni-utils
# $APT_GET_INSTALL proj-bin
# $APT_GET_INSTALL proj-data
# $APT_GET_INSTALL va-driver-all
# $APT_GET_INSTALL vdpau-driver-all


###############################################################################
# Install build dependencies that are necessary for install_pip_dependencies.sh
# and install_compiled_dependencies.sh
###############################################################################
#
# NOTE: every package that is installed here must be removed in
# cleanup_build_dependencies.sh

# General build dependencies (notably useful for pip-compiled packages)
$APT_GET_INSTALL cmake
$APT_GET_INSTALL g++
$APT_GET_INSTALL gcc
$APT_GET_INSTALL git
$APT_GET_INSTALL libc-dev
$APT_GET_INSTALL libpython2.7-dev
$APT_GET_INSTALL make

# Build dependencies for MIRCen's fork of openslide
$APT_GET_INSTALL autoconf automake libtool
$APT_GET_INSTALL pkg-config  # needed for auto(re)conf (to compile openslide)
$APT_GET_INSTALL libopenjp2-7-dev  # for openslide
$APT_GET_INSTALL libtiff-dev  # for openslide
$APT_GET_INSTALL libcairo2-dev libgdk-pixbuf2.0-dev libglib2.0-dev libxml2-dev
$APT_GET_INSTALL libjxr-dev  # needed for compiling MIRCen's fork of openslide

# Build dependencies of libXp
$APT_GET_INSTALL x11proto-print-dev

# Build dependencies of python-pcl
$APT_GET_INSTALL libpcl-dev  # for python-pcl

# Build dependencies of SIP/PyQt
$APT_GET_INSTALL qtwebengine5-dev  # for PyQt


###############################################################################
# Free disk space by removing APT caches
###############################################################################

$APT_GET clean

if [ -z "$APT_NO_LIST_CLEANUP" ]; then
    # delete all the apt list files since they're big and get stale quickly
    $SUDO rm -rf /var/lib/apt/lists/*
fi