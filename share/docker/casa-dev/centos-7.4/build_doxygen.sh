#! /bin/sh

# This script builds doxygen
__download=1
__install=1
__install_prefix=/usr/local
__build_proc_num=4
__tmp_dir=/tmp
__download_dir=${__tmp_dir}
__build_dir=${__tmp_dir}

pushd ${__tmp_dir}

# ------------------------------------------------------------------------------
# doxygen
# ------------------------------------------------------------------------------
DOXYGEN_VERSION=1.8.7
DOXYGEN_INSTALL_PREFIX=${__install_prefix}
DOXYGEN_SOURCE_URL=${DOXYGEN_MIRROR_URL:-ftp://ftp.stack.nl/pub/users/dimitri}/doxygen-${DOXYGEN_VERSION}.src.tar.gz

echo "=============================== DOXYGEN ================================"
if [ "${__download}" == "1" ]; then
    wget ${DOXYGEN_SOURCE_URL} -O ${__download_dir}/doxygen-${DOXYGEN_VERSION}.tar.gz
fi

if [ "${__install}" == "1" ]; then
    tar xvf ${__download_dir}/doxygen-${DOXYGEN_VERSION}.tar.gz
    pushd ${__build_dir}/doxygen-${DOXYGEN_VERSION}
 
    ./configure --prefix=${DOXYGEN_INSTALL_PREFIX} || exit 1
    make -j${__build_proc_num} || exit 1
    make -j${__build_proc_num} install || exit 1

    popd
    
    \rm -rf ${__build_dir}/doxygen-${DOXYGEN_VERSION} \
            ${__download_dir}/doxygen-${DOXYGEN_VERSION}.tar.gz
fi
