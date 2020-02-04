#! /bin/sh

# This script builds a minimal libnetcdf, with fewer dependencies than the
# system one on Ubuntu in /tmp/netcdf_build, then copies libs
# in /tmp/netcdf.
# It is intended to run in a docker container (casa-dev image) with /tmp
# mounted on a host filesystem so that the built libs can be copied somewhere
# else, typically in the sources of casa-test images.
# Use the host-side script: build_mesa_host.sh to run this one inside docker.

# NETCDF_VERSION=4.4.1.1
# OLD=
NETCDF_VERSION=4.3.1
OLD=
# netcdf 4.3.1 is not available any longer on the official ftp
URL=ftp://ftp.cea.fr/pub/dsv/anatomist/devinstaller/packages/

cd /tmp
wget $URL/${OLD}netcdf-$NETCDF_VERSION.tar.gz || exit 1
tar xvf netcdf-$NETCDF_VERSION.tar.gz
# build usinf configure
cd netcdf-c-$NETCDF_VERSION
CPPFLAGS=-I/usr/include/mpi ./configure --prefix=/usr/local/netcdf-$NETCDF_VERSION --enable-shared --enable-netcdf4 --disable-pnetcdf --disable-cxx-4 --disable-dap --disable-fortran --disable-cxx --disable-static --disable-utilities
make -j4
make -j4 install
cd ..
rm -Rf netcdf-c-$NETCDF_VERSION netcdf-$NETCDF_VERSION.tar.gz
ln -s netcdf-$NETCDF_VERSION /usr/local/netcdf
cd /usr/local/lib
ln -s ../netcdf/lib/*.so* .
cd pkgconfig
ln -s ../../netcdf/lib/pkgconfig/*.pc .
cd ../..
ln -s ../netcdf/include/netcdf.h /usr/local/include/
