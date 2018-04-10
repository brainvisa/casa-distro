#! /bin/sh

# This script builds a software-only mesa libGL inside a docker container,
# and gets the built libs in /tmp
# The built libs can be copied somewhere else, typically in the sources of
# casa-test images.

cd $(dirname $0)
mkdir /tmp/mesa_libs
docker run --rm -v /tmp/mesa_libs:/tmp/mesa_libs -v $(pwd)/build_mesa.sh:/tmp/build_mesa.sh -u $(id -u):$(id -g) -e USER=$USER cati/casa-dev:ubuntu-12.04 sh /tmp/build_mesa.sh
