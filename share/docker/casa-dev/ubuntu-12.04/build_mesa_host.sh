#! /bin/sh

# This script builds a software-only mesa libGL inside a docker container,
# and gets the built libs in /tmp
# The built libs can be copied somewhere else, typically in the sources of
# casa-test images.

cd $(dirname $0)
docker run --rm -v /tmp:/tmp -v $(pwd)/build_mesa.sh:/tmp/build_mesa.sh cati/casa-dev:ubuntu-12.04 sh /tmp/build_mesa.sh
