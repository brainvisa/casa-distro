#! /bin/bash
#
# Install dependencies for image casa-run-5.1. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image supports a Python 3 / Qt 6 build of BrainVISA.
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
    wget
)
$SUDO apt-get -o Acquire::Retries=5 install --no-install-recommends -y \
      ${early_dependencies[@]}


###############################################################################
# Install runtime dependencies with apt-get
###############################################################################

# $SUDO apt-get -o Acquire::Retries=3 update

# Generally useful packages
generally_useful_packages=(
    curl
    file
    less
    lsb-release
    ssh-client  # notably useful for Git repositories over SSH
    sudo
    tree
    unzip
    vim
    nano
    python3
    python-is-python3
    x11-utils   # xdpyinfo
    mesa-utils  # glxinfo
)

# Dynamic libraries needed at runtime for OpenGL in the container
gl_dependencies=(
    libglapi-mesa
    libgl1
    libglib2.0-0
    libglu1-mesa
    libx11-6
    libllvm18
    libunwind8
)


###############################################################################
# Install build dependencies that are necessary for install_pip_dependencies.sh
# and install_compiled_dependencies.sh
###############################################################################

# The build_dependencies bash array variable is defined in build_dependencies.sh, which is sourced at the top of this script.


# Hopefully, using a large value for Acquire::Retries can solve the infamous
# 101st package issue (fetching more than 100 packages in a single apt-get
# invocation sometimes fails in NeuroSpin, probably due to flaky firewall
# rules).
$SUDO apt-get -o Acquire::Retries=20 install --no-install-recommends -y \
    ${generally_useful_packages[@]} \
    ${gl_dependencies[@]} \
    ${build_dependencies[@]}

###############################################################################
# Free disk space by removing APT caches
###############################################################################

$SUDO apt-get clean

if [ -z "$APT_NO_LIST_CLEANUP" ]; then
    # delete all the apt list files since they're big and get stale quickly
    $SUDO rm -rf /var/lib/apt/lists/*
fi

###############################################
# Fix a /dev/pts problem on Ubuntu 22.04
###############################################

# without this any sudo will fail with an error
# "unable to allocate pty: Operation not permitted"

$SUDO mount devpts /dev/pts -t devpts || true


###############################################
# install pixi
###############################################

$SUDO rm -rf /var/lib/apt/lists/*
export PIXI_HOME=/usr/local
$SUDO bash -c 'curl -fsSL https://pixi.sh/install.sh | sh'
