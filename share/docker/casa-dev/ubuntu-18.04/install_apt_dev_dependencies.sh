#! /bin/bash
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
# Install development packages with apt-get
###############################################################################

export DEBIAN_FRONTEND=noninteractive

# setup best mirror in /etc/apt/sources.list
# $SUDO python2 -m pip --no-cache-dir install apt-mirror-updater
# $SUDO apt-mirror-updater -a

$SUDO apt-get -o Acquire::Retries=3 update

# Probably obsolete packages (TODO: remove)
# apt-utils
# gadfly  # obsolete dep? (only used in datamind)
# libgsl-dev  # was used in highres-cortex (only?)
# openjdk-8-jdk  # was used for Docbook docs
# pyro  # obsolete since soma-workflow 3

# A selection of packages that were in cati/casa-dev:ubuntu-18.04 before Yann's
# rewrite of the install scripts (in the runtime_image branch). TODO: check if
# these packages should be installed here, or maybe in the casa-run image.
packages_to_review=(
    # fakeroot
    # fonts-liberation  # graphviz recommends it but works without
    # gsfonts
    # libcairo2-dev
    # libdouble-conversion-dev
    # libgraphviz-dev
    # libgstreamer-plugins-good1.0-0
    # libgtk2.0-dev
    libmpich-dev
    # libncurses5-dev
    # libqt5sensors5-dev
    # libqt5svg5-dev
    # libqt5waylandclient5-dev
    # libqt5websockets5-dev
    # libqt5webview5-dev
    # libqt5xmlpatterns5-dev
    # libxcb-icccm4-dev
    # libxcb-image0-dev
    # libxcb-keysyms1-dev
    # libxcb-render-util0-dev
    # libxcb-shm0-dev
    # libxcb-util-dev
    # libxcb-xinerama0-dev
    # libxcb-xkb-dev
    # libxcomposite-dev
    # libxcursor-dev
    # libxi-dev
    # libxinerama-dev
    # libxrandr-dev
    # libzmq3-dev
    # lmodern  # recommended by texlive-base
    mpich
    # python-pytest
    # python-sqlalchemy-ext
    # python3-numexpr
    # python3-pytest
    # python3-simplejson
    # python3-tables
    # qttranslations5-l10n
    # tex-gyre  # recommended by texlive-fonts-recommended
    # x11-xserver-utils
    # x11proto-composite-dev
    # x11proto-gl-dev
    # x11proto-input-dev
    # x11proto-randr-dev
    # x11proto-xinerama-dev
)


# Source version control
version_control_packages=(
    git
    git-lfs
    subversion
)

# Configure/build toolchain
toolchain_packages=(
    automake
    clang
    cmake
    cmake-curses-gui
    g++
    gcc
    gfortran
    libc-dev
    make
    pkg-config
    qt5-default
    # Compiled and installed in install_compiled_dev_dependencies.sh because of a
    # bug in the SIP version supplied in APT.
    #
    # python-sip-dev
    # python3-sip-dev
)

# Development tools and convenience utilities
development_tools=(
    bash-completion
    flake8
    gdb
    gdbserver
    gedit
    gitg
    gitk
    kate
    kdesdk-scripts  # contains the 'colorsvn' script (is it really worth it? the dependencies of kdesdk-scripts are huge...)
    kdiff3
    kompare
    kwrite
    locate
    meld
    nano
    python-autopep8
    python-dbg
    spyder
    vim
    xterm
)

# TODO: review and add -dbg packages that contain the debug symbols
# corresponding to installed -dev packages.
debug_symbol_packages=(
    libc6-dbg  # recommended by gdb
)

# Documentation building
documentation_building_packages=(
    doxygen
    ghostscript
    graphviz
    pandoc
    python-epydoc
    # python-sphinx  # installed with PIP
    texlive-latex-base
    texlive-fonts-recommended
    wkhtmltopdf
)

# Python 3 packages
python3_packages=(
    python3-crypto
    python3-cryptography
    python3-html2text
    python3-openpyxl
    python3-traits
    python3-pip
    python3-configobj
    python3-sphinx
    python3-sphinx-paramlinks
    python3-pandas
    python3-pil  # used in anatomist, morphologist, nuclear_imaging, snapbase
    python3-xmltodict
    python3-sqlalchemy
    python3-mysqldb
    python3-ipython-genutils
    python3-requests
    python3-jenkins
    python3-opengl
    python3-joblib
    python3-tqdm

    # These packages used to be installed with PIP, presumably because they
    # depend on NumPy, but it seems that they do not depend on a particular ABI
    # version.
    python3-nibabel
    python3-pyparsing
    python3-pydot
    python3-dicom  # version 0.9.9 from Ubuntu, NOT python-pydicom

    # These packages used to be installed with PIP, but that was probably a
    # careless copy/paste from the Ubuntu 16.04 scripts.
    cython3
    python3-xlrd
    python3-xlwt

    # The following dependencies are installed with pip for various reasons,
    # see install_pip_dev_dependencies.sh.
    #
    # TODO: when upgrading the base system (i.e. switching to Ubuntu 20.04),
    # check that they work when installed with apt.
    #
    # python3-nipype
    # python3-jenkinsapi
    #
    # python3-zmq
    # python3-ipython
    # python3-jupyter-client
    # python3-qtconsole
    # python3-nbsphinx
    # python3-sphinx-gallery
    #
    # python3-numpy
    # python3-scipy
    # python3-skimage
    # python3-sklearn
    # python3-fastcluster

    # PyYAML is installed with pip because pre-commit requires a more recent
    # version. If we install it here, pip complains that it cannot reliably
    # uninstall it.
    #
    # python3-yaml

    # SIP and PyQT are compiled in install_compiled_dev_dependencies.sh to work
    # around a bug in the APT version of sip 4.19 concerning virtual C++
    # inheritance.
    #
    # pyqt5-dev
    # pyqt5-dev-tools
    # python3-pyqt5
    # python3-pyqt5.qtmultimedia
    # python3-pyqt5.qtopengl
    # python3-pyqt5.qtsvg
    # python3-pyqt5.qtwebkit
    # python3-pyqt5.qtsql
    # python3-pyqt5.qtwebsockets
    # python3-pyqt5.qtxmlpatterns
    # python3-pyqt5.qtx11extras
)


# Development packages of compiled libraries (C/C++/Fortran) that are used by
# components of the 'standard' BrainVISA distribution (these are the libraries
# that are looked up by the find_* statements in the CMake files of BrainVISA
# projects, excluding the packages that belong to other categories, like Python
# or documentation building packages).
brainvisa_standard_dev_dependencies=(
    libasound2-dev
    libboost-dev
    libboost-filesystem-dev
    libboost-system-dev
    libdcmtk-dev
    libexpat1-dev
    libgl1-mesa-dev
    libglib2.0-dev
    libglu1-mesa-dev
    libjpeg-dev
    libminc-dev
    # libnetcdf-dev  # compiled in the casa-run image
    libomp-dev  # OpenMP with the clang compiler
    libopenjp2-7-dev
    libpng-dev
    libqt5x11extras5-dev
    libqwt-qt5-dev
    libsigc++-2.0-dev
    libsvm-dev
    libtiff-dev
    libvtk6-dev
    libvtk6-qt-dev
    libxml2-dev
    qttools5-dev
    qtmultimedia5-dev
    qttools5-dev-tools
    zlib1g-dev
    # Other packages that are searched in CMake files using find_*, but were
    # not included in the older casa-dev images:
    #
    # libxml++2.6-dev
    # swig
)


brainvisa_toolboxes_dev_dependencies=(
)


# Other dependencies of BrainVISA projects, which are not directly referred to
# in the projects' CMakeLists.txt, but are packaged as third-party libraries.
#
# FIXME: this category should eventually disappear: if these are really
# dependencies, they should be added to the corresponding CMakeList.txt
brainvisa_probable_dev_dependencies=(
    libblas-dev
    libeigen3-dev
    libhdf5-mpi-dev
    liblapack-dev
    libnifti-dev
    libpcl-dev
    libqt5webkit5-dev
    mpi-default-dev
    qtwebengine5-dev
)

$SUDO apt-get -o Acquire::Retries=20 install --no-install-recommends -y \
    ${version_control_packages[@]} \
    ${toolchain_packages[@]} \
    ${development_tools[@]} \
    ${debug_symbol_packages[@]} \
    ${documentation_building_packages[@]} \
    ${python3_packages[@]} \
    ${brainvisa_standard_dev_dependencies[@]} \
    ${brainvisa_toolboxes_dev_dependencies[@]} \
    ${brainvisa_probable_dev_dependencies[@]}


###############################################################################
# Free disk space by removing APT caches
###############################################################################

$SUDO apt-get clean

if [ -z "$APT_NO_LIST_CLEANUP" ]; then
    # delete all the apt list files since they're big and get stale quickly
    $SUDO rm -rf /var/lib/apt/lists/*
fi
