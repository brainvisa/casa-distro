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
else
    SUDO=sudo
fi

# Defines the build_dependencies bash array variable, which is used at the
# bottom of this script (see below). The build_dependencies.sh file is expected
# to be found in the same directory as this script.
. "$(dirname -- "$0")"/build_dependencies.sh


###############################################################################
# Install dependencies of this script and configure repositories
###############################################################################

export DEBIAN_FRONTEND=noninteractive

$SUDO apt-get -o Acquire::Retries=3 update

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


###############################################################################
# Install runtime dependencies with apt-get
###############################################################################

$SUDO apt-get -o Acquire::Retries=3 update


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
    python-pip
    python-setuptools  # needed for most source installs with python-pip
    ssh-client  # notably useful for Git repositories over SSH
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
    python-mysqldb
    python-openpyxl
    python-paramiko
    python-requests
    # python-six  # installed by pip (Ubuntu 18.04 ships 1.11.0, we need >= 1.13)
    python-sqlalchemy
    python-traits
    python-xmltodict
    python-yaml

    # These packages used to be installed with PIP, presumably because they
    # depend on NumPy, but it seems that they do not depend on a particular ABI
    # version.
    python-nipype
    python-nibabel
    python-pyparsing
    python-pydot
    python-jenkinsapi
    python-pydicom

    # These packages used to be installed with PIP, but that was probably a
    # careless copy/paste from the Ubuntu 16.04 scripts.
    cython
    python-xlrd
    python-xlwt
    python-pandas

    # The following dependencies are installed with pip for various reasons,
    # see install_pip_dependencies.sh.
    #
    # TODO: when upgrading the base system (i.e. switching to Ubuntu 20.04),
    # check that they work when installed with apt.
    #
    # python-zmq
    # python-ipython
    # python-jupyter-client
    # python-qtconsole
    # python-nbsphinx
    # python-sphinx-gallery
    #
    # python-numpy
    # python-dipy
    # python-fastcluster
    # python-h5py
    # python-matplotlib
    # python-scipy
    # python-skimage
    # python-sklearn

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


###############################################################################
# Install build dependencies that are necessary for install_pip_dependencies.sh
# and install_compiled_dependencies.sh
###############################################################################

# The build_dependencies bash array variable is defined in build_dependencies.sh, which is sourced at the top of this script.
#
# . build_dependencies.sh


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

$SUDO apt-get clean

if [ -z "$APT_NO_LIST_CLEANUP" ]; then
    # delete all the apt list files since they're big and get stale quickly
    $SUDO rm -rf /var/lib/apt/lists/*
fi
