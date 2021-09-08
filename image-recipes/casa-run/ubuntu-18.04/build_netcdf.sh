#! /bin/sh

set -e
set -x

# This script builds a minimal libnetcdf, with fewer dependencies than the
# system one on Ubuntu in /tmp/netcdf_build, then install the libs in
# /usr/local.

NETCDF_VERSION=4.6.1
OLD=
# NETCDF_VERSION=4.1.1
# OLD=old/
# netcdf 4.6.1 is not available any longer on the official ftp
URL=ftp://ftp.cea.fr/pub/dsv/anatomist/devinstaller/packages/

cd /tmp
wget $URL/${OLD}netcdf-$NETCDF_VERSION.tar.gz || exit 1
tar xvf netcdf-$NETCDF_VERSION.tar.gz
mkdir netcdf_build
cd netcdf_build
cmake ../netcdf-c-$NETCDF_VERSION -DCMAKE_INSTALL_PREFIX=/usr/local/netcdf-$NETCDF_VERSION -DBUILD_TESTING=OFF -DBUILD_TESTSETS=OFF -DBUILD_UTILITIES=OFF -DCMAKE_BUILD_TYPE=Release -DENABLE_DAP=OFF -DENABLE_EXAMPLES=OFF -DENABLE_TESTS=OFF -DHAVE_HDF5_H=/usr/include/hdf5/serial
make -j4
sudo make -j4 install
cd ..
rm -Rf netcdf_build netcdf-c-$NETCDF_VERSION netcdf-$NETCDF_VERSION.tar.gz
ln -s netcdf-$NETCDF_VERSION /usr/local/netcdf
cd /usr/local/lib
ln -s ../netcdf/lib/*.so* .
cd pkgconfig
ln -s ../../netcdf/lib/pkgconfig/*.pc .
cd ../../include
ln -s ../netcdf/include/*.h .
cd ..
