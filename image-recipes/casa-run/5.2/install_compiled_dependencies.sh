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
Cflags: -I${includedir}/jxrlib -D__ANSI__ -DDISABLE_PERF_MEASUREMENT
EOF
cd "$tmp"
git clone --depth=1 https://github.com/MIRCen/openslide.git
cd openslide
autoreconf --install
PKG_CONFIG_PATH="$tmp/pkgconfig" ./configure
make -j$(nproc)
sudo make install


###############################################################################
# Post-install configuration
###############################################################################

sudo ldconfig
