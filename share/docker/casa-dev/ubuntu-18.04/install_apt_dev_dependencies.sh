#! /bin/bash
# Install system dependencies for image cati/casa-dev:ubuntu-18.04
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them

###############################################################################
# Install system packages with apt-get
###############################################################################

export DEBIAN_FRONTEND=noninteractive
APT_GET_INSTALL="sudo apt-get -o Acquire::Retries=3 install --no-install-recommends -y"

# setup best mirror in /etc/apt/sources.list
# sudo python2 -m pip --no-cache-dir install apt-mirror-updater
# sudo apt-mirror-updater -a

sudo apt-get -o Acquire::Retries=3 update

# WARNING: it is necessary to call apt-get install separately for small groups
# of packages to avoid the mysterious 101st package issue (Download of the
# 101st package fails randomly in NeuroSpin, maybe due to firewall issues).
#
# TODO: as indirect dependencies were removed from this list, it may be that
# some lines trigger the installation of more than 100 packages. If this is the
# case, we have to re-introduce indirect dependencies here, but this time we
# will *explicitly* mark them as such, to avoid ever having to disentangle this
# mess again...
#
# TODO: check that the APT option -o Acquire::Retries fixes the 101st package
# issue

# Probably obsolete packages (TODO: remove)
# $APT_GET_INSTALL apt-utils
# $APT_GET_INSTALL gadfly  # obsolete dep? (only used in datamind)
# $APT_GET_INSTALL libgsl-dev  # was used in highres-cortex (only?)
# $APT_GET_INSTALL openjdk-8-jdk  # was used for Docbook docs
# $APT_GET_INSTALL pyro  # obsolete since soma-workflow 3

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
$APT_GET_INSTALL pkg-config
# Compiled and installed in install_compiled_dev_dependencies.sh because of a
# bug in the SIP version supplied in APT.
#
# $APT_GET_INSTALL python-sip-dev
# $APT_GET_INSTALL python3-sip-dev

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
$APT_GET_INSTALL pandoc
$APT_GET_INSTALL python-epydoc
$APT_GET_INSTALL python-sphinx
$APT_GET_INSTALL texlive-latex-base
$APT_GET_INSTALL texlive-fonts-recommended
$APT_GET_INSTALL wkhtmltopdf

# Framework-specific tools
$APT_GET_INSTALL qt5-default


# Python 3 packages
$APT_GET_INSTALL python3-matplotlib
# Compiled and installed in install_compiled_dev_dependencies.sh because of a
# bug in the SIP version supplied in APT.
#
# $APT_GET_INSTALL pyqt5-dev
# $APT_GET_INSTALL pyqt5-dev-tools
# $APT_GET_INSTALL python3-pyqt5
# $APT_GET_INSTALL python3-pyqt5.qtmultimedia
# $APT_GET_INSTALL python3-pyqt5.qtopengl
# $APT_GET_INSTALL python3-pyqt5.qtsvg
# $APT_GET_INSTALL python3-pyqt5.qtwebkit
# $APT_GET_INSTALL python3-pyqt5.qtsql
# $APT_GET_INSTALL python3-pyqt5.qtwebsockets
# $APT_GET_INSTALL python3-pyqt5.qtxmlpatterns
# $APT_GET_INSTALL python3-pyqt5.qtx11extras
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
$APT_GET_INSTALL python3-ipython-genutils
# PyYAML is installed with pip because pre-commit requires a more recent
# version. If we install it here, pip complains that it cannot reliably
# uninstall it.
#
# $APT_GET_INSTALL python3-yaml
$APT_GET_INSTALL python3-requests
$APT_GET_INSTALL python3-jenkins
$APT_GET_INSTALL python3-opengl
$APT_GET_INSTALL python3-joblib
$APT_GET_INSTALL python3-tqdm
$APT_GET_INSTALL python3-dicom
# TODO: The following packages used to be installed with pip, check that the APT versions work correctly
$APT_GET_INSTALL cython3
$APT_GET_INSTALL python3-numpy
$APT_GET_INSTALL python3-zmq
$APT_GET_INSTALL python3-ipython
$APT_GET_INSTALL python3-jupyter-client
$APT_GET_INSTALL python3-qtconsole
$APT_GET_INSTALL python3-scipy
$APT_GET_INSTALL python3-nbsphinx
$APT_GET_INSTALL python3-sphinx-gallery
$APT_GET_INSTALL python3-nibabel
$APT_GET_INSTALL python3-skimage
$APT_GET_INSTALL python3-sklearn
$APT_GET_INSTALL python3-pyparsing
$APT_GET_INSTALL python3-pydot
$APT_GET_INSTALL python3-pydicom
$APT_GET_INSTALL python3-fastcluster



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
)

sudo apt-get -o Acquire::Retries=10 install --no-install-recommends -y \
    ${brainvisa_standard_dev_dependencies[@]} \
    ${brainvisa_toolboxes_dev_dependencies[@]} \
    ${brainvisa_probable_dev_dependencies[@]}


sudo apt-get clean
# delete all the apt list files since they're big and get stale quickly
sudo rm -rf /var/lib/apt/lists/*
