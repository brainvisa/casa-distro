#! /bin/bash
# Install system dependencies for image casa-dev-5.1
#
# NOTE: This script is run during the creation of the Singularity and
# VirtualBox casa-run image. Make sure not to include anything specific to a
# given virtualization/containerization engine  in this file.

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

$SUDO apt-get -o Acquire::Retries=3 update
$SUDO apt-get -o Acquire::Retries=5 install \
      --no-remove --no-install-recommends -y \
    apt-transport-https  # required for the PackageCloud git-lfs repository
curl -L https://packagecloud.io/github/git-lfs/gpgkey | $SUDO apt-key add -
cat <<EOF | $SUDO tee /etc/apt/sources.list.d/git-lfs.list
deb https://packagecloud.io/github/git-lfs/ubuntu/ bionic main
EOF
$SUDO apt-get -o Acquire::Retries=3 update

# A selection of packages that were in casa-dev-5.0 before Yann's
# rewrite of the install scripts (in the runtime_image branch).
packages_to_review=(
    libmpich-dev
    mpich
)

# Source version control
version_control_packages=(
    git
    git-lfs
    git-man
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
    pyqt5-dev
    pyqt5-dev-tools
    python3-sip-dev
    qt5-default
)

# Development tools and convenience utilities
development_tools=(
    ack-grep
    bash-completion
    emacs-nox
    flake8
    gdb
    gdbserver
    gedit
    git-man
    gitg
    gitk
    kate
    kdiff3
    kompare
    kwrite
    locate
    meld
    nano
    python2-minimal  # only for flake8 tests of casa-distro
    python3-autopep8
    python3-dbg
    python3-objgraph
    spyder
    strace
    tox
    vim
    xterm
    xdot
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
    jupyter-nbconvert
    pandoc
    python3-sphinx
    python3-sphinx-gallery
    texlive-latex-base
    texlive-fonts-recommended
    wkhtmltopdf
)

# Development packages of compiled libraries (C/C++/Fortran) that are used by
# components of the 'standard' BrainVISA distribution (these are the libraries
# that are looked up by the find_* statements in the CMake files of BrainVISA
# projects, excluding the packages that belong to other categories, like Python
# or documentation building packages).
brainvisa_standard_dev_dependencies=(
    libasound2-dev
    libblitz0-dev
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
    libnetcdf-dev
    libomp-dev  # OpenMP with the clang compiler
    libopenjp2-7-dev
    libpng-dev
    libqt5x11extras5-dev
    libqwt-qt5-dev
    libsigc++-2.0-dev
    libspnav-dev
    libsvm-dev
    libtiff-dev
    libvtk7-dev
    libvtk7-qt-dev
    libxml2-dev
    qttools5-dev
    qtmultimedia5-dev
    qttools5-dev-tools
    zlib1g-dev
)


brainvisa_toolboxes_dev_dependencies=(
    # Required for building MRtrix3
    libqt5svg5-dev
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

$SUDO apt-get -o Acquire::Retries=20 install \
      --no-remove --no-install-recommends -y \
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
