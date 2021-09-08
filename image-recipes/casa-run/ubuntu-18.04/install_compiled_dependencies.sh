#! /bin/sh
#
# Install dependencies for image cati/casa-run:ubuntu-18.04. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image contains Python 2 and Qt 5.
#
# NOTE: This script is also run during the creation of the VirtualBox casa-run
# image. Make sure not to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them


###############################################################################
# Compile and install dependencies that are must be built from source
###############################################################################


# Blitz++ is not provided anymore as an APT package in Debian/Ubuntu
cd /tmp
wget https://github.com/blitzpp/blitz/archive/1.0.2.tar.gz
tar -zxf 1.0.2.tar.gz
mkdir blitz-1.0.2/build
cd blitz-1.0.2
autoreconf -i
./configure
make -j$(nproc)
sudo make install
cd ..
rm -rf 1.0.2.tar.gz blitz-1.0.2


# install libXp, used by some external software (SPM...)
#
# TODO: check if this is still needed, this library is not required by recent
# versions of SPM12 at least
cd /tmp
wget https://mirror.umd.edu/ubuntu/pool/main/libx/libxp/libxp_1.0.2.orig.tar.gz
tar xf libxp_1.0.2.orig.tar.gz
cd libXp-1.0.2
./configure
make -j$(nproc)
sudo make install
cd /tmp
rm -R libxp_1.0.2.orig.tar.gz libXp-1.0.2


# MIRCen's fork of openslide with support for CZI format
cd /tmp
git clone --depth=1 https://github.com/MIRCen/openslide.git
cd openslide
autoreconf --install
./configure
make -j$(nproc)
sudo make install
cd /tmp
rm -rf openslide


# install a version of netcdf with fewer dependencies
#
# /opt is used instead of /tmp here because /tmp can be bind mount during build
# on Singularity. Therfore previously copied files are hidden.
sudo bash /opt/build_netcdf.sh


cd /tmp
wget https://github.com/strawlab/python-pcl/archive/v0.2.0.zip
unzip v0.2.0.zip
cd python-pcl-0.2.0
cat > setup.patch << EOF
16c16
< PCL_SUPPORTED = ["-1.7", "-1.6", ""]    # in order of preference
---
> PCL_SUPPORTED = ["-1.8", "-1.7", "-1.6", ""]    # in order of preference
EOF
patch -p0 setup.py < setup.patch
sudo python2 -m pip install .
cd ..
rm -rf python-pcl-0.2.0 v0.2.0.zip
# rm -rf python-pcl-0.3.0rc1 v0.3.0rc1.zip

# cmake does not work with clang whenever Qt5 is invoked.
# workaround here:
# https://stackoverflow.com/questions/38027292/configure-a-qt5-5-7-application-for-android-with-cmake/40256862#40256862
tmpfile=$(mktemp)
sed 's/^\(set_property.*INTERFACE_COMPILE_FEATURES.*\)$/#\ \1/' < /usr/lib/x86_64-linux-gnu/cmake/Qt5Core/Qt5CoreConfigExtras.cmake >| "$tmpfile"
sudo cp -f "$tmpfile" /usr/lib/x86_64-linux-gnu/cmake/Qt5Core/Qt5CoreConfigExtras.cmake
rm -f "$tmpfile"

# reinstall an older sip and PyQt5 from sources because of a bug in sip 4.19
# and virtual C++ inheritance
PY=2.7 PY_S=2.7 sh /opt/build_sip_pyqt.sh


###############################################################################
# Post-install configuration
###############################################################################

sudo ldconfig
