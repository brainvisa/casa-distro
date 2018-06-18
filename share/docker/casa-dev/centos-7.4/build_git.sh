#! /bin/sh

# This script builds git
__download=1
__install=1
__install_prefix=/usr/local
__build_proc_num=4
__tmp_dir=/tmp
__download_dir=${__tmp_dir}
__build_dir=${__tmp_dir}

pushd ${__tmp_dir}

# ------------------------------------------------------------------------------
# git
# ------------------------------------------------------------------------------
GIT_VERSION=2.7.4
GIT_INSTALL_PREFIX=${__install_prefix}
GIT_SOURCE_URL=https://mirrors.edge.kernel.org/pub/software/scm/git/git-${GIT_VERSION}.tar.gz

echo "=============================== GIT ================================"
if [ "${__download}" == "1" ]; then
    wget ${GIT_SOURCE_URL} -O ${__download_dir}/git-${GIT_VERSION}.tar.gz
fi

if [ "${__install}" == "1" ]; then
    tar xvf ${__download_dir}/git-${GIT_VERSION}.tar.gz
    pushd ${__build_dir}/git-${GIT_VERSION}
 
    ./configure --prefix=${GIT_INSTALL_PREFIX} || exit 1
    make -j${__build_proc_num} || exit 1
    make -j${__build_proc_num} install || exit 1

    popd
    
    \rm -rf ${__build_dir}/git-${GIT_VERSION} \
            ${__download_dir}/git-${GIT_VERSION}.tar.gz
fi
