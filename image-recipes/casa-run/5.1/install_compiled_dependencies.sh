#! /bin/sh
#
# Install dependencies for image casa-run-5.0. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image contains Python 3 and Qt 5.
#
# NOTE: This script is also run during the creation of the VirtualBox casa-run
# image. Make sure not to include anything Docker-specific in this file.

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


# Blitz++ is not provided anymore as an APT package in Debian/Ubuntu
cd "$tmp"
wget https://github.com/blitzpp/blitz/archive/1.0.2.tar.gz
tar -zxf 1.0.2.tar.gz
mkdir blitz-1.0.2/build
cd blitz-1.0.2
autoreconf -i
./configure
make -j$(nproc)
sudo make install


# install libXp, used by some external software (SPM...)
#
# TODO: check if this is still needed, this library is not required by recent
# versions of SPM12 at least
cd "$tmp"
wget https://mirror.umd.edu/ubuntu/pool/main/libx/libxp/libxp_1.0.2.orig.tar.gz
tar xf libxp_1.0.2.orig.tar.gz
cd libXp-1.0.2
./configure
make -j$(nproc)
sudo make install


# MIRCen's fork of openslide with support for CZI format
#
# Openslide needs the pkgconfig file for libjxr, which is not in the Ubuntu
# packages until Ubuntu 22.04.
mkdir -p "$tmp/pkgconfig"
cat <<'EOF' > "$tmp/pkgconfig/libjxr.pc"
prefix=/usr
exec_prefix=${prefix}
libdir=${exec_prefix}/lib
includedir=${prefix}/include

Name: libjxr
Description: A library for reading JPEG XR images.

Version: 1.1
Libs: -L${libdir} -ljpegxr -ljxrglue
Libs.private: -lm
Cflags: -I${includedir}/libjxr -D__ANSI__ -DDISABLE_PERF_MEASUREMENT
EOF
cd "$tmp"
git clone --depth=1 https://github.com/MIRCen/openslide.git
cd openslide
autoreconf --install
PKG_CONFIG_PATH="$tmp/pkgconfig" ./configure
make -j$(nproc)
sudo make install


# install a version of netcdf with fewer dependencies
#
# /opt is used instead of /tmp here because /tmp can be bind mount during build
# on Singularity. Therefore previously copied files are hidden.
sudo bash /opt/build_netcdf.sh


cd "$tmp"
wget https://github.com/strawlab/python-pcl/archive/v0.2.0.zip
unzip -o v0.2.0.zip
cd python-pcl-0.2.0
cat > setup.patch << EOF
16c16
< PCL_SUPPORTED = ["-1.7", "-1.6", ""]    # in order of preference
---
> PCL_SUPPORTED = ["-1.8", "-1.7", "-1.6", ""]    # in order of preference
EOF
patch -p0 setup.py < setup.patch
sudo python3 -m pip install .
cd ..
rm -rf python-pcl-0.2.0 v0.2.0.zip
# rm -rf python-pcl-0.3.0rc1 v0.3.0rc1.zip

# cmake does not work with clang whenever Qt5 is invoked.
# workaround here:
# https://stackoverflow.com/questions/38027292/configure-a-qt5-5-7-application-for-android-with-cmake/40256862#40256862
tmpfile=$tmp/Qt5CoreConfigExtras.cmake
sed 's/^\(set_property.*INTERFACE_COMPILE_FEATURES.*\)$/#\ \1/' < /usr/lib/x86_64-linux-gnu/cmake/Qt5Core/Qt5CoreConfigExtras.cmake >| "$tmpfile"
sudo cp -f "$tmpfile" /usr/lib/x86_64-linux-gnu/cmake/Qt5Core/Qt5CoreConfigExtras.cmake

# reinstall an older sip and PyQt5 from sources because of a bug in sip 4.19
# and virtual C++ inheritance
PY=3.6m PY_S=3.6 sh /opt/build_sip_pyqt.sh


###############################################################################
# Post-install configuration
###############################################################################

sudo ldconfig
