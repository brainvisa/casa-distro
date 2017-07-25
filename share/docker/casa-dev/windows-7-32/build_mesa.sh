#! /bin/sh

# This script builds a software-only mesa libGL in /tmp/mesa, then copies libs
# in /tmp.
# It is intended to run in a docker container (casa-dev image) with /tmp
# mounted on a host filesystem so that the built libs can be copied somewhere
# else, typically in the sources of casa-test images.
# Use the host-side script: build_mesa_host.sh to run this one inside docker.

__build_proc_num=$(($(lscpu -p | grep -v '#' | wc -l) - 1))

cd /tmp
wget ftp://ftp.freedesktop.org/pub/mesa/mesa-17.0.0.tar.gz
tar xvf mesa-17.0.0.tar.gz
cd mesa-17.0.0
./configure --enable-glx=xlib --disable-dri --disable-egl --with-gallium-drivers=swrast --disable-gbm --disable-gles1 --disable-gles2 --prefix=/tmp/mesa
make -j${__build_proc_num}
make install
cd ..
cp /tmp/mesa/lib/libGL.so.1 /tmp/mesa/lib/libglapi.so.0 /tmp/mesa_libs/

# 32 bit variant
cd /tmp/mesa-17.0.0
make clean
CXXFLAGS=-m32 CFLAGS=-m32 LDFLAGS=-m32 ./configure --host=i386-linux-gnu --build=i386-linux-gnu --enable-glx=xlib --disable-dri --disable-egl --with-gallium-drivers=swrast --disable-gbm --disable-gles1 --disable-gles2 --prefix=/tmp/mesa32
make -j${__build_proc_num}
make install
cd ..
mkdir /tmp/mesa_libs/i386
cp /tmp/mesa32/lib/libGL.so.1 /tmp/mesa32/lib/libglapi.so.0 /tmp/mesa_libs/i386

cd ..
rm -Rf mesa-17.0.0