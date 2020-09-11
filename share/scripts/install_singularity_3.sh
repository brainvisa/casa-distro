#!/usr/bin/env bash

pushd /tmp

export OS=linux
export ARCH=amd64
export SUDO=sudo

if [ -z "${GOPATH}" ]; then
    # Set default GOPATH
    export GOPATH="/volatile/a-sac-ns-brainvisa/go"
fi

if [ -z "${INSTALL_PREFIX}" ]; then
    INSTALL_PREFIX=/usr/local
fi

if [ -z "${INSTALL_GO}" ]; then
    if [ -z "$(which go)" ]; then
        INSTALL_GO=1
    fi
fi 

if [ "${INSTALL_GO}" -eq "1" ]; then
    # Install go
    echo "Installing go ..."
    export GO_VERSION=1.13 
    wget https://dl.google.com/go/go${GO_VERSION}.${OS}-${ARCH}.tar.gz && \
    ${SUDO} tar -C /usr/local -xzvf go${GO_VERSION}.${OS}-${ARCH}.tar.gz && \
    rm go${GO_VERSION}.${OS}-${ARCH}.tar.gz
fi


# Install singularity 3.6.2
echo "Installing singularity ..."
SINGULARITY_VERSION=3.6.2
if [ -z "${SINGULARITY_INSTALL_PREFIX}" ]; then
    SINGULARITY_INSTALL_PREFIX=${INSTALL_PREFIX}/singularity-${SINGULARITY_VERSION}
fi

wget https://github.com/hpcng/singularity/releases/download/v${SINGULARITY_VERSION}/singularity-${SINGULARITY_VERSION}.tar.gz -O singularity-${SINGULARITY_VERSION}.tar.gz && \
tar xvf singularity-${SINGULARITY_VERSION}.tar.gz && \
rm singularity-${SINGULARITY_VERSION}.tar.gz && \
pushd singularity && \
./mconfig --prefix=${SINGULARITY_INSTALL_PREFIX} && \
make -C ./builddir && \
${SUDO} make -C ./builddir install && \
popd

popd