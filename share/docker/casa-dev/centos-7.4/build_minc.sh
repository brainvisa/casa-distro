#! /bin/sh

# This script builds the libminc
__download=1
__install=1
__install_prefix=/usr/local
__build_proc_num=4
__tmp_dir=/tmp
__download_dir=${__tmp_dir}
__build_dir=${__tmp_dir}

pushd ${__tmp_dir}

# ------------------------------------------------------------------------------
# minc
# ------------------------------------------------------------------------------
MINC_VERSION=2.2.00
MINC_INSTALL_PREFIX=${__install_prefix}
MINC_SOURCE_URL=http://packages.bic.mni.mcgill.ca/tgz/minc-${MINC_VERSION}.tar.gz

echo "========================= MINC =============================="
if [ "${__download}" == "1" ]; then
    wget ${MINC_SOURCE_URL} -O ${__download_dir}/minc-${MINC_VERSION}.tar.gz
fi

if [ "${__install}" == "1" ]; then
    tar xvf ${__download_dir}/minc-${MINC_VERSION}.tar.gz
    pushd ${__build_dir}/minc-${MINC_VERSION}

    mkdir -p build
    pushd build
    cmake -DCMAKE_INSTALL_PREFIX=${MINC_INSTALL_PREFIX} \
          -DMINC2_BUILD_SHARED_LIBS=ON \
          -DMINC2_BUILD_TOOLS=OFF \
          .. \
    || exit 1

    make -j${__build_proc_num} install || exit 1
    popd
    popd

    \rm -rf ${__build_dir}/minc-${MINC_VERSION} \
            ${__download_dir}/minc-${MINC_VERSION}.tar.gz
fi
