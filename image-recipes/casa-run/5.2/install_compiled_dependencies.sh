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


###############################################################################
# Compile and install dependencies that are must be built from source
###############################################################################

# MIRCen's fork of openslide with support for CZI format
#
# Openslide needs the pkgconfig file for libjxr, which is not in the Ubuntu
# packages until Ubuntu 22.04.
mkdir -p /tmp/pkgconfig
cat <<'EOF' > /tmp/pkgconfig/libjxr.pc
prefix=/usr
exec_prefix=${prefix}
libdir=${exec_prefix}/lib
includedir=${prefix}/include

Name: libjxr
Description: A library for reading JPEG XR images.

Version: 1.1
Libs: -L${libdir} -ljpegxr -ljxrglue
Libs.private: -lm
Cflags: -I${includedir}/libjxr/common -I${includedir}/libjxr/image/x86 -I${includedir}/libjxr/image -I${includedir}/libjxr/glue -I${includedir}/libjxr/test -D__ANSI__ -DDISABLE_PERF_MEASUREMENT
EOF
cd /tmp
git clone --depth=1 https://github.com/MIRCen/openslide.git
cd openslide
autoreconf --install
PKG_CONFIG_PATH=/tmp/pkgconfig ./configure
make -j$(nproc)
sudo make install
cd /tmp
rm -rf openslide
rm -rf /tmp/pkgconfig


###############################################################################
# Post-install configuration
###############################################################################

sudo ldconfig
