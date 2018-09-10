#! /bin/sh

# This script builds openmpi
__download=1
__install=1
__install_prefix=/usr/local
__build_proc_num=4
__tmp_dir=/tmp
__download_dir=${__tmp_dir}
__build_dir=${__tmp_dir}

pushd ${__tmp_dir}

# ------------------------------------------------------------------------------
# openmpi
# ------------------------------------------------------------------------------
OPENMPI_VERSION=2.0.4
OPENMPI_INSTALL_PREFIX=${__install_prefix}
OPENMPI_SOURCE_URL=${OPENMPI_MIRROR_URL:-https://download.open-mpi.org/release/open-mpi/v2.0}/openmpi-${OPENMPI_VERSION}.tar.bz2

echo "=============================== OPENMPI ================================"
if [ "${__download}" == "1" ]; then
    wget ${OPENMPI_SOURCE_URL} -O ${__download_dir}/openmpi-${OPENMPI_VERSION}.tar.bz2
fi

if [ "${__install}" == "1" ]; then
    tar xvf ${__download_dir}/openmpi-${OPENMPI_VERSION}.tar.bz2
    pushd ${__build_dir}/openmpi-${OPENMPI_VERSION}
 
    libtoolize --force \
    && aclocal \
    && autoheader \
    && automake --force-missing --add-missing \
    && autoconf \
    && ./configure \
            --prefix=${OPENMPI_INSTALL_PREFIX} \
            --enable-shared \
    || exit 1
    make -j${__build_proc_num} install || exit 1

    popd
    
    \rm -rf ${__build_dir}/openmpi-${OPENMPI_VERSION} \
            ${__download_dir}/openmpi-${OPENMPI_VERSION}.tar.gz
fi
