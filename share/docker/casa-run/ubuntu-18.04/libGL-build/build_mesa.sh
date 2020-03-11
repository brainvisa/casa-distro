#! /bin/sh

# This script builds a software-only mesa libGL in /tmp/mesa, then copies libs
# in /tmp.
# It is intended to run in a docker container (casa-dev image) with /tmp
# mounted on a host filesystem so that the built libs can be copied somewhere
# else, typically in the sources of casa-test images.
# Use the host-side script: build_mesa_host.sh to run this one inside docker.

cd /tmp
wget ftp://ftp.freedesktop.org/pub/mesa/mesa-17.0.0.tar.gz
tar xvf mesa-17.0.0.tar.gz
cd mesa-17.0.0
./configure --enable-glx=xlib --disable-dri --disable-egl --with-gallium-drivers=swrast --disable-gbm --prefix=/tmp/mesa
make
make install
cd ..
rm -Rf mesa-17.0.0
cp /tmp/mesa/lib/libGL.so.1 /tmp/mesa/lib/libglapi.so.0 /tmp/mesa_libs/
