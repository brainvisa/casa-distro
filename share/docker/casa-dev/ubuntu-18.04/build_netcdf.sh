#! /bin/sh

# This script builds a minimal libnetcdf, with fewer dependencies than the
# system one on Ubuntu in /tmp/netcdf_build, then copies libs
# in /tmp/netcdf.
# It is intended to run in a docker container (casa-dev image) with /tmp
# mounted on a host filesystem so that the built libs can be copied somewhere
# else, typically in the sources of casa-test images.
# Use the host-side script: build_mesa_host.sh to run this one inside docker.

NETCDF_VERSION=4.4.1.1
OLD=
# NETCDF_VERSION=4.1.1
# OLD=old/

cd /tmp
wget ftp://ftp.unidata.ucar.edu/pub/netcdf/${OLD}netcdf-$NETCDF_VERSION.tar.gz
tar xvf netcdf-$NETCDF_VERSION.tar.gz
mkdir netcdf_build
cd netcdf_build
cmake ../netcdf-$NETCDF_VERSION -DCMAKE_INSTALL_PREFIX=/usr/local/netcdf-$NETCDF_VERSION -DBUILD_TESTING=OFF -DBUILD_TESTSETS=OFF -DBUILD_UTILITIES=OFF -DCMAKE_BUILD_TYPE=Release -DENABLE_DAP=OFF -DENABLE_EXAMPLES=OFF -DENABLE_TESTS=OFF
make -j4
make -j4 install
cd ..
rm -Rf netcdf_build netcdf-$NETCDF_VERSION netcdf-$NETCDF_VERSION.tar.gz
ln -s netcdf-$NETCDF_VERSION /usr/local/netcdf
cd /usr/local/lib
ln -s ../netcdf/lib/*.so* .
cd pkgconfig
ln -s ../../netcdf/lib/pkgconfig/*.pc .
cd ../../include
ln -s ../netcdf/include/*.h .
cd ..
