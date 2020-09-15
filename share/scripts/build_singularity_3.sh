#!/usr/bin/env bash

set -e  # stop the script on error
set -x  # display commands before running them

pushd /tmp

# Assign default values
: ${OS:=linux} ${ARCH:=amd64} ${SUDO:=sudo}
: ${SINGULARITY_VERSION=3.6.2} ${GO_VERSION:=1.15.2}
: ${INSTALL_PREFIX=/usr/local}


if [ -z "${INSTALL_GO}" ]; then
    if [ -z "$(which go)" ]; then
        INSTALL_GO=1
    fi
fi

if [ "${INSTALL_GO}" -eq "1" ]; then
    # Install go
    echo "Installing go ${GO_VERSION} in /tmp/go ..."
    wget https://dl.google.com/go/go${GO_VERSION}.${OS}-${ARCH}.tar.gz
    ${SUDO} tar -C /tmp -xzf go${GO_VERSION}.${OS}-${ARCH}.tar.gz
    rm go${GO_VERSION}.${OS}-${ARCH}.tar.gz
    PATH=/tmp/go/bin:${PATH}
fi

if [ -z "${GOPATH}" ]; then
    # Set default GOPATH
    GOPATH="/tmp/.go/cache"
fi

export PATH GOPATH

# Install singularity 3.6.2
echo "Installing singularity ${SINGULARITY_VERSION} ..."
wget https://github.com/hpcng/singularity/releases/download/v${SINGULARITY_VERSION}/singularity-${SINGULARITY_VERSION}.tar.gz -O singularity-${SINGULARITY_VERSION}.tar.gz
tar -zxf singularity-${SINGULARITY_VERSION}.tar.gz
rm singularity-${SINGULARITY_VERSION}.tar.gz
pushd singularity
./mconfig --prefix="${INSTALL_PREFIX}"
make -C ./builddir
${SUDO} make -C ./builddir install
popd
rm -rf singularity
rm -rf /tmp/go
rm -rf /tmp/.go

popd
