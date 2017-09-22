# Dockerfile for image cati/brainvisa-dev:windows-7-32

FROM cati/casa-test:windows-7-32

# Directory containing thirdparty dependencies
ENV CASA_DEPS=/casa/deps
# Directory containing all files used to configure a build directory (svn passwords, bv_maker.cfg, etc.)
ENV CASA_CONF=/casa/conf
# Directory containing source code
ENV CASA_SRC=/casa/src
# Directory containing all files that are necessary only for building (source tree, build dir, etc.)
ENV CASA_BUILD=/casa/build
# Installation directory
ENV CASA_INSTALL=/casa/install
# Installation directory
ENV CASA_PACK=/casa/pack
# Default bv_maker branch
ENV CASA_BRANCH=latest_release
# Tests data directory
ENV CASA_TESTS=/casa/tests
# Custom projects
ENV CASA_CUSTOM_SRC=/casa/custom/src
ENV CASA_CUSTOM_BUILD=/casa/custom/build

# Copy script to cross compile thirdparty dependencies
COPY install_ubuntu_14.04_crossbuild.sh /tmp/install_ubuntu_14.04_crossbuild.sh

RUN chmod +x /tmp/install_ubuntu_14.04_crossbuild.sh

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    cmake-curses-gui \
    subversion \
    git \
    python-dev \
    qt4-dev-tools \
    qt4-designer \
    qt4-qmake \
    qt4-qmlviewer \
    qt4-qtconfig \
    qt4-linguist-tools \
    sqlite3 \
    graphviz \
    graphviz-dev \
    doxygen \
    libxml2-utils \
    python-qt4-dev \
    python-pexpect \
    python-sphinx \
    openjdk-7-jdk \
    vim \
    nano \
    wget \
    automake \
    texlive-fonts-recommended \
    lftp \
    apt-utils \
    libxslt-dev \
    gdb \
    python-setuptools \
    kdesdk-scripts \
    net-tools \
    locate \
    gcc-multilib \
    g++-multilib \
    python-mako \
    libx11-dev:i386 \
    libxext-dev:i386 \
  && CROSSBUILD_INSTALL_PREFIX=${CASA_DEPS} \
     CROSSBUILD_UPDATE_REGISTRY_PATH=0 \
     CROSSBUILD_ARCH=i686 \
     SYSTEM=1 \
     MINGW64=1 \
     /tmp/install_ubuntu_14.04_crossbuild.sh \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/tmp.*

# ipython / jupyter
RUN easy_install pip

# build thirdparty dependencies
RUN \
    CROSSBUILD_INSTALL_PREFIX=${CASA_DEPS} \
    CROSSBUILD_UPDATE_REGISTRY_PATH=1 \
    CROSSBUILD_ARCH=i686 \
    PYTHON=1 \
    /tmp/install_ubuntu_14.04_crossbuild.sh \
 && wineserver -k -w \
 && rm -rf /tmp/tmp.*
 
RUN \
    CROSSBUILD_INSTALL_PREFIX=${CASA_DEPS} \
    CROSSBUILD_UPDATE_REGISTRY_PATH=0 \
    CROSSBUILD_ARCH=i686 \
    CROSSBUILD_LIBS=1 \
    /tmp/install_ubuntu_14.04_crossbuild.sh \
 && wineserver -k -w \
 && rm -rf /tmp/tmp.*

RUN \
    CROSSBUILD_INSTALL_PREFIX=${CASA_DEPS} \
    CROSSBUILD_UPDATE_REGISTRY_PATH=0 \
    CROSSBUILD_ARCH=i686 \
    CROSSBUILD_PYTHON_MODULES=1 \
    /tmp/install_ubuntu_14.04_crossbuild.sh \
 && wineserver -k -w \
 && rm -rf /tmp/tmp.*
 

# Install Qt Installer Framework (prebuilt on Mandriva 2008)
RUN cd /tmp \
  && wget http://brainvisa.info/static/qt_installer-1.6.tar.gz \
  && cd /usr/local \
  && tar xfz /tmp/qt_installer-1.6.tar.gz \
  && ln -s qt_installer-1.6 qt_installer \
  && cd /usr/local/bin \
  && ln -s ../qt_installer/bin/* . \
  && rm /tmp/qt_installer-1.6.tar.gz


COPY svn.secret $CASA_CONF/svn.secret
COPY svn /usr/local/bin/svn
RUN chmod +x /usr/local/bin/svn

# allow attach gdb to a process
RUN echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# newer additions, to be placed in the other apt line, later
# RUN apt-get update && apt-get install something-dev
