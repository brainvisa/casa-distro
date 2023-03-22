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
MESA_VERSION=22.0.5  # same version as distributed with Ubuntu 22.04
MESA_FILENAME=mesa-${MESA_VERSION}.tar.xz
MESA_SHA256SUM=5ee2dc06eff19e19b2867f12eb0db0905c9691c07974f6253f2f1443df4c7a35
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
meson \
    -D glx=xlib \
    -D gallium-drivers=swrast \
    -D platforms=x11 \
    -D dri3=false \
    -D dri-drivers= \
    -D vulkan-drivers= \
    -D buildtype=release
ninja
mkdir /usr/local/lib/mesa
cp -d src/gallium/targets/libgl-xlib/libGL.so \
   src/gallium/targets/libgl-xlib/libGL.so.1 \
   src/gallium/targets/libgl-xlib/libGL.so.1.5.0 \
   /usr/local/lib/mesa
cd ../..
rm -rf mesa-"$MESA_VERSION"


# MIRCen's fork of openslide with support for CZI format
#
cd "$tmp"
git clone --depth=1 https://github.com/MIRCen/openslide.git
cd openslide
autoreconf --install
./configure
make -j$(nproc)
sudo make install

# reinstall an older sip and PyQt5 from sources because of a bug in sip 4.19.25
# and virtual C++ inheritance
PY=3.10 PY_S=3.10 sh /build/build_sip_pyqt.sh

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


# install draco lib (meshes compression lib)
cd "$tmp"
wget https://github.com/google/draco/archive/refs/tags/1.5.6.tar.gz
tar xf 1.5.6.tar.gz
rm -f 1.5.6.tar.gz
wget https://github.com/gulrak/filesystem/archive/refs/tags/v1.5.14.tar.gz
tar xf v1.5.14.tar.gz
rm -f v1.5.14.tar.gz
wget https://github.com/syoyo/tinygltf/archive/refs/tags/v2.8.3.tar.gz
tar xf v2.8.3.tar.gz
rm -f v2.8.3.tar.gz
# install quick and dirty thirdparty deps
mv filesystem-1.5.14/include draco-1.5.6/third_party/filesystem/
mv tinygltf-2.8.3/*.h tinygltf-2.8.3/*.hpp draco-1.5.6/third_party/tinygltf/
mkdir draco-build
cd draco-build
cmake -DCMAKE_CXX_FLAGS:STRING="-fPIC -DDRACO_ATTRIBUTE_VALUES_DEDUPLICATION_SUPPORTED=1 -DDRACO_ATTRIBUTE_INDICES_DEDUPLICATION_SUPPORTED=1" -DCMAKE_INSTALL_PREFIX:PATH=/usr/local -DCMAKE_BUILD_TYPE=Release -DDRACO_ANIMATION_ENCODING=ON -DDRACO_BACKWARDS_COMPATIBILITY=ON -DDRACO_DECODER_ATTRIBUTE_DEDUPL=ON -DDRACO_FAST=ON -DDRACO_GLTF_BITSTREAM=ON -DDRACO_IE_COMPATIBLE=ON -DDRACO_JS_GLUE=ON -DDRACO_MESH_COMPRESSION=ON -DDRACO_POINT_CLOUD_COMPRESSION=ON -DDRACO_PREDICTIVE_EDGEBREAKER=ON -DDRACO_STANDARD_EDGEBREAKER=ON -DDRACO_TESTS=OFF -DDRACO_TRANSCODER_SUPPORTED=ON -DDRACO_WASM=ON -DDRACO_EIGEN_PATH=/usr/include/eigen3 ../draco-1.5.6
make -j$(nproc)
sudo make install

# needed for DarcoPy
sudo pip3 install scikit-build

# install DracoPy
cd "$tmp"
git clone --depth=1 -b decode_texture https://github.com/denisri/DracoPy.git
cd DracoPy
export CPPFLAGS="-I/usr/local/include -DDRACO_ATTRIBUTE_VALUES_DEDUPLICATION_SUPPORTED=1 -DDRACO_ATTRIBUTE_INDICES_DEDUPLICATION_SUPPORTED=1"
export LDFLAGS="-L/usr/local/lib -ldraco"
python3 setup.py build
sudo python3 setup.py install --prefix /usr/local


###############################################################################
# Post-install configuration
###############################################################################

sudo ldconfig
