#! /bin/sh

# This script builds blitz
__download=1
__install=1
__install_prefix=/usr/local
__build_proc_num=4
__tmp_dir=/tmp
__download_dir=${__tmp_dir}
__build_dir=${__tmp_dir}

pushd ${__tmp_dir}

# ------------------------------------------------------------------------------
# blitz
# ------------------------------------------------------------------------------
BLITZ_VERSION=0.10
BLITZ_INSTALL_PREFIX=${__install_prefix}
BLITZ_SOURCE_URL=${BLITZ_MIRROR_URL:-http://sourceforge.mirrorservice.org/b/bl/blitz/blitz/Blitz%2B%2B%20${BLITZ_VERSION}}/blitz-${BLITZ_VERSION}.tar.gz

echo "=============================== BLITZ ================================"
if [ "${__download}" == "1" ]; then
    wget ${BLITZ_SOURCE_URL} -O ${__download_dir}/blitz-${BLITZ_VERSION}.tar.gz
fi

if [ "${__install}" == "1" ]; then
    tar xvf ${__download_dir}/blitz-${BLITZ_VERSION}.tar.gz
    pushd ${__build_dir}/blitz-${BLITZ_VERSION}
 
    libtoolize --force \
    && aclocal \
    && autoheader \
    && automake --force-missing --add-missing \
    && autoconf \
    && ./configure \
            --prefix=${BLITZ_INSTALL_PREFIX} \
            --enable-shared \
    || exit 1
    make -j${__build_proc_num} install || exit 1

    popd
    
    \rm -rf ${__build_dir}/blitz-${BLITZ_VERSION} \
            ${__download_dir}/blitz-${BLITZ_VERSION}.tar.gz
fi
