#! /bin/sh

# This script builds a more recent version of boost than the one of
# Ubuntu 12.04 system, which is required by some of BrainVisa projects

BOOST_VERSION=1.65.1
BOOST_VERSION_FILENAME=1_65_1

cd /tmp
wget https://dl.bintray.com/boostorg/release/${BOOST_VERSION}/source/boost_${BOOST_VERSION_FILENAME}.tar.bz2
tar xfj boost_${BOOST_VERSION_FILENAME}.tar.bz2
cd boost_${BOOST_VERSION_FILENAME}
./bootstrap.sh
./b2 -j4 install
cd ..
rm -Rf boost_${BOOST_VERSION_FILENAME} boost_${BOOST_VERSION_FILENAME}.tar.bz2
