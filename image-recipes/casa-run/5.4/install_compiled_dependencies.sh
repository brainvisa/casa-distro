#! /bin/sh
#
# Install dependencies for image casa-run-5.1. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image supports a Python 3 / Qt 5 build of BrainVISA.
#
# NOTE: This script is run during the creation of the Singularity and
# VirtualBox casa-run image. Make sure not to include anything specific to a
# given virtualization/containerization engine  in this file.

set -e  # stop the script on error
set -x  # display commands before running them

# Set up a temporary directory that is cleaned up properly upon exiting
tmp=
cleanup() {
    status=$?
    if [ -d "$tmp" ]; then
        # Use "|| :" to allow failure despite "set -e"
        chmod -R u+rwx "$tmp" || :  # allow removal of read-only directories
        rm -rf "$tmp" || :
    fi
    return $status
}
trap cleanup EXIT
trap 'cleanup; trap - HUP EXIT; kill -HUP $$' HUP
trap 'cleanup; trap - INT EXIT; kill -INT $$' INT
trap 'cleanup; trap - TERM EXIT; kill -TERM $$' TERM
# SIGQUIT should not cause temporary files to be deleted, because they may be
# useful for debugging. Other resources should still be released.
trap 'trap - QUIT EXIT; kill -QUIT $$' QUIT

tmp=$(mktemp -d)


###############################################################################
# Compile and install dependencies that are must be built from source
###############################################################################

# install libXp, used by some external software (old SPM, AFNI, ...)
# well it seems pretty impossible to install on Ubuntu 22.04:
# it needs printproto (Xprint) which is deprecated for decades,
# and has no install procedure any longer (see
# https://gitlab.freedesktop.org/xorg/proto/printproto)
# cd "$tmp"
# wget https://mirror.umd.edu/ubuntu/pool/main/libx/libxp/libxp_1.0.2.orig.tar.gz
# tar xf libxp_1.0.2.orig.tar.gz
# cd libXp-1.0.2
# ./configure
# make -j$(nproc)
# sudo make install


# Install a software-rendering-only libGL to work around compatibility issues
# e.g. with X2Go, see https://github.com/brainvisa/casa-distro/issues/321.
# This corresponds to the opengl=software option of 'bv'.
# MESA_VERSION=22.0.5  # same version as distributed with Ubuntu 22.04
MESA_VERSION=24.0.9  # same version as distributed with Ubuntu 24.04
MESA_FILENAME=mesa-${MESA_VERSION}.tar.xz
# MESA_SHA256SUM=5ee2dc06eff19e19b2867f12eb0db0905c9691c07974f6253f2f1443df4c7a35
MESA_SHA256SUM=51aa686ca4060e38711a9e8f60c8f1efaa516baf411946ed7f2c265cd582ca4c
cd "$tmp"
wget "https://archive.mesa3d.org/$MESA_FILENAME"
if ! [ "$(sha256sum "$MESA_FILENAME")" \
           = "$MESA_SHA256SUM  $MESA_FILENAME" ]; then
    echo "ERROR: checksum of $MESA_FILENAME does not match." 2>&1
    exit 1
fi
tar -Jxf "$MESA_FILENAME"
cd mesa-"$MESA_VERSION"
mkdir build
cd build
meson setup \
    -D glx=xlib \
    -D gallium-drivers=swrast \
    -D platforms=x11 \
    -D dri3=disabled \
    -D vulkan-drivers= \
    -D buildtype=release
ninja
mkdir /usr/local/lib/mesa
cp -d src/gallium/targets/libgl-xlib/libGL.so \
   src/gallium/targets/libgl-xlib/libGL.so.1 \
   src/gallium/targets/libgl-xlib/libGL.so.1.5.0 \
   /usr/local/lib/mesa
cd ../..
rm -rf mesa-"$MESA_VERSION" "$MESA_FILENAME"


# MIRCen's fork of openslide with support for CZI format
#
cd "$tmp"
git clone --depth=1 https://github.com/MIRCen/openslide.git
cd openslide
LANGUAGE="C" LANG="C" autoreconf --install
./configure
make -j$(nproc)
sudo make install
cd ..
rm -rf openslide

# reinstall libminc 4.0.0 because newer versions can't properly read freesurfer
# .mgz files
cd "$tmp"
git clone https://github.com/BIC-MNI/libminc.git --single-branch --branch libminc-2-3-00
cd libminc
cmake . -DHDF5_INCLUDE_DIR=/usr/include/hdf5/serial -DHDF5_LIBRARY=/usr/lib/x86_64-linux-gnu/libhdf5_serial.so -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release -DLIBMINC_BUILD_SHARED_LIBS=ON -DLIBMINC_MINC1_SUPPORT=ON
make -j$(nproc)
sudo make install
cd ..
rm -rf libminc


###############################################################################
# Post-install configuration
###############################################################################

sudo ldconfig
