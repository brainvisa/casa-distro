#! /bin/bash
#
# Install dependencies for image cati/casa-run:ubuntu-18.04. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image supports a Python 2 / Qt 5 build of BrainVISA.
#
# NOTE: This script is also run during the creation of the VirtualBox casa-run
# image. Make sure not to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them

if [ $(id -u) -eq 0 ]; then
    SUDO=
    APT_GET="apt-get -o Acquire::Retries=3"
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

# Packages that are needed later by this script
early_dependencies=(
    ca-certificates  # needed by wget to download over https
    gnupg  # needed by apt-key
    libglu1-mesa  # dependency of virtualgl
    libxtst6  # dependency of virtualgl
    libxv1  # dependency of virtualgl
    wget
)
$SUDO apt-get -o Acquire::Retries=5 install --no-install-recommends -y \
      ${early_dependencies[@]}


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


# Runtime dependencies of FSL
fsl_runtime_dependencies=(
    bc
    dc
    libopenblas-base
    tcsh
)

# Runtime dependencies of MATLAB
matlab_runtime_dependencies=(
    lsb-core
    libxext6
    libxt6
    libxmu6
)

# Generally useful packages
generally_useful_packages=(
    ca-certificates
    curl
    file
    less
    lsb-release
    sudo
    unzip
    wget
    xz-utils
)

# Dependencies of headless Anatomist
headless_anatomist_dependencies=(
    # libx11-xcb1
    # libfontconfig1
    # libdbus-1-3
    # libxrender1
    # libglib2.0-0
    # libxi6
    mesa-utils
    x11-utils
    xvfb
)

cd /tmp
wget https://sourceforge.net/projects/virtualgl/files/2.6.3/virtualgl_2.6.3_amd64.deb
$SUDO dpkg -i virtualgl_2.6.3_amd64.deb
rm -f /tmp/virtualgl_2.6.3_amd64.deb


# Python packages needed at runtime by BrainVISA
brainvisa_python_runtime_dependencies=(
    python-dicom
    python-matplotlib
    python-mysqldb
    python-openpyxl
    python-paramiko
    python-requests
    python-setuptools
    # python-six  # installed by pip (Ubuntu 18.04 ships 1.11.0, we need >= 1.13)
    python-sqlalchemy
    python-traits
    python-xmltodict
    python-yaml

    # TODO: the following dependencies used to be installed with pip, check that
    # they work when installed with apt
    cython
    python-numpy
    python-zmq
    python-ipython
    python-jupyter-client
    python-qtconsole
    python-scipy
    python-nbsphinx
    python-sphinx-gallery
    python-nipype
    python-dipy
    python-nibabel
    python-skimage
    python-sklearn
    python-pyparsing
    python-pydot
    python-jenkinsapi
    python-pydicom
    python-fastcluster
    python-backports.functools-lru-cache

    # SIP and PyQT are compiled in install_compiled_dependencies.sh to work
    # around a bug in the APT version of sip 4.19 concerning virtual C++
    # inheritance.
    #
    # python-sip
    # python-pyqt5
    # python-pyqt5.qtmultimedia
    # python-pyqt5.qtopengl
    # python-pyqt5.qtsvg
    # python-pyqt5.qtwebkit
    # python-pyqt5.qtsql
    # python-pyqt5.qtwebsockets
    # python-pyqt5.qtxmlpatterns
)


# Dynamic libraries needed at runtime by BrainVISA
#
# This list is generated **automatically** with the list-shared-libs-paths.sh
# script. In a container where the whole BrainVISA tree has been compiled, run
# the following commands to generate this list:
#
# $ find /casa/build -type f -execdir sh -c - 'if file -b "$1"|grep ^ELF >/dev/null 2>&1; then /casa/list-shared-libs-paths.sh "$1"; fi' - {} \; | tee ~/all-shared-libs-paths.txt
# $ sort -u < ~/all-shared-libs-paths.txt | while read path; do dpkg -S "$path" 2>/dev/null; done | sed -e 's/\([^:]*\):.*$/\1/' | sort -u
#
# Please DO NOT add other packages to this list, so that it can be wiped and
# regenerated easily. If other libraries are needed, consider creating a new
# variable to store them.
brainvisa_shared_library_dependencies=(
    libc6
    libdcmtk12
    libexpat1
    libgcc1
    libgfortran4
    libglu1-mesa
    libjpeg-turbo8
    libminc2-4.0.0
    libopenjp2-7
    libpython2.7
    libqt5core5a
    libqt5gui5
    libqt5multimedia5
    libqt5network5
    libqt5opengl5
    libqt5sql5
    libqt5widgets5
    libqwt-qt5-6
    libsigc++-2.0-0v5
    libstdc++6
    libsvm3
    libtiff5
    libxml2
    zlib1g
)

# Programs and data that BrainVISA depends on at runtime
brainvisa_misc_runtime_dependencies=(
    python2.7
    lftp
    sqlite3
    xbitmaps
)

# Dependencies that are needed for running BrainVISA tests in casa-run
brainvisa_test_dependencies=(
    cmake  # BrainVISA tests are driven by ctest
)


# Dubious packages (TODO: check if they are really needed)
# libbdplus0
# libbluray2
# libavcodec57
# libavformat57
# libavformat-dev
# libavutil55
# libchromaprint1
# libcrystalhd3
# libgme0
# libgsm1
# libmp3lame0
# libmpg123-0
# libnetcdf-c++4
# libnl-route-3-200
# libogdi3.2
# libopenmpt0
# libopenni0
# libopenni2-0
# libopenni-sensor-pointclouds0
# libpq5
# libproj12
# libpsm-infinipath1
# librdmacm1
# libshine3
# libsoxr0
# libspatialite7
# libspeex1
# libsuperlu5
# libswresample2
# libswscale4
# libtwolame0
# libutempter0
# libtinyxml2.6.2v5
# libva-drm2
# libva-x11-2
# libva2
# libvdpau1
# libvorbisfile3
# libvpx5
# libwavpack1
# libx264-152
# libx265-146
# libxvidcore4
# libzvbi-common
# libzvbi0
# mesa-va-drivers
# mesa-vdpau-drivers
# odbcinst
# odbcinst1debian2
# openni-utils
# proj-bin
# proj-data
# va-driver-all
# vdpau-driver-all
# vtk6


###############################################################################
# Install build dependencies that are necessary for install_pip_dependencies.sh
# and install_compiled_dependencies.sh
###############################################################################
#
# NOTE: every package that is on this list should be removed in
# cleanup_build_dependencies.sh


build_dependencies=(
    # General build dependencies (notably useful for pip-compiled packages)
    # cmake  # required in brainvisa_test_dependencies
    g++
    gcc
    git
    libc-dev
    libpython2.7-dev
    make
    python-pip
    python-setuptools

    # Build dependencies of MIRCen's fork of openslide
    autoconf
    automake
    libtool
    pkg-config  # needed for autoreconf
    libopenjp2-7-dev
    libtiff-dev
    libcairo2-dev
    libgdk-pixbuf2.0-dev
    libglib2.0-dev
    libxml2-dev
    libjxr-dev

    # Build dependencies of libXp
    x11proto-print-dev

    # Build dependencies of python-pcl
    libpcl-dev  # for python-pcl

    # Build dependencies of SIP/PyQt
    qtwebengine5-dev  # for PyQt
)


# Hopefully, using a large value for Acquire::Retries can solve the infamous
# 101st package issue (fetching more than 100 packages in a single apt-get
# invocation sometimes fails in NeuroSpin, probably due to flaky firewall
# rules).
$SUDO apt-get -o Acquire::Retries=20 install --no-install-recommends -y \
    ${fsl_runtime_dependencies[@]} \
    ${matlab_runtime_dependencies[@]} \
    ${generally_useful_packages[@]} \
    ${headless_anatomist_dependencies[@]} \
    ${brainvisa_misc_runtime_dependencies[@]} \
    ${brainvisa_test_dependencies[@]} \
    ${brainvisa_python_runtime_dependencies[@]} \
    ${brainvisa_shared_library_dependencies[@]} \
    ${build_dependencies[@]}


###############################################################################
# Free disk space by removing APT caches
###############################################################################

$APT_GET clean

if [ -z "$APT_NO_LIST_CLEANUP" ]; then
    # delete all the apt list files since they're big and get stale quickly
    $SUDO rm -rf /var/lib/apt/lists/*
fi
