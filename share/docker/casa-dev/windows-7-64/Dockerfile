# Dockerfile for image cati/brainvisa-dev:windows-7-64

FROM cati/casa-test:windows-7-64

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
    cmake-curses-gui \
    qt4-dev-tools \
    qt4-designer \
    qt4-qmake \
    qt4-qmlviewer \
    qt4-qtconfig \
    qt4-linguist-tools \
    sqlite3 \
    python-qt4-dev \
    python-pexpect \
    openjdk-7-jdk \
    vim \
    nano \
    texlive-fonts-recommended \
    lftp \
    gdb \
    kdesdk-scripts \
    net-tools \
    locate \
    gcc-multilib \
    g++-multilib \
    libx11-dev:i386 \
    libxext-dev:i386 \
  && CROSSBUILD_INSTALL_PREFIX=${CASA_DEPS} \
     CROSSBUILD_UPDATE_REGISTRY_PATH=0 \
     CROSSBUILD_ARCH=x86_64 \
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
    CROSSBUILD_ARCH=x86_64 \
    PYTHON=1 \
    /tmp/install_ubuntu_14.04_crossbuild.sh \
 && wineserver -k -w \
 && rm -rf /tmp/tmp.*
 
RUN \
    CROSSBUILD_INSTALL_PREFIX=${CASA_DEPS} \
    CROSSBUILD_UPDATE_REGISTRY_PATH=0 \
    CROSSBUILD_ARCH=x86_64 \
    CROSSBUILD_LIBS=1 \
    /tmp/install_ubuntu_14.04_crossbuild.sh \
 && wineserver -k -w \
 && rm -rf /tmp/tmp.*

RUN \
    CROSSBUILD_INSTALL_PREFIX=${CASA_DEPS} \
    CROSSBUILD_UPDATE_REGISTRY_PATH=0 \
    CROSSBUILD_ARCH=x86_64 \
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

# Install doxygen (prebuilt)
RUN cd /tmp \
  && wget http://brainvisa.info/static/doxygen-1.8.7-linux.tar.gz \
  && cd /usr/local \
  && tar xfz /tmp/doxygen-1.8.7-linux.tar.gz \
  && ln -sf doxygen-1.8.7 doxygen \
  && cd /usr/local/bin \
  && ln -sf ../doxygen/bin/* . \
  && rm /tmp/doxygen-1.8.7-linux.tar.gz

# Add jenkins package
RUN pip install python_jenkins==0.4.15
  
COPY svn.secret $CASA_CONF/svn.secret
COPY svn /usr/local/bin/svn
RUN chmod +x /usr/local/bin/svn

# allow attach gdb to a process
RUN echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# Install a version of brainvisa-cmake
RUN svn export https://bioproj.extra.cea.fr/neurosvn/brainvisa/development/brainvisa-cmake/branches/bug_fix /c/tmp/brainvisa-cmake && \
    cd /c/tmp/brainvisa-cmake && \
    cmake -G 'MSYS Makefiles' -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/bug_fix && \
    make install && cd .. && rm -r /c/tmp/brainvisa-cmake

# Set PATH to have bv_env_host being either the one of the build directory (/casa/build)
# or the one in the image (/casa/brainvisa-cmake)
ENV PATH=${PATH}:/casa/build/bin:/casa/brainvisa-cmake/bin

# Set variable to make bv_maker use /casa/conf/bv_maker.cfg by default
ENV BRAINVISA_BVMAKER_CFG=/casa/conf/bv_maker.cfg

# newer additions, to be placed in the other apt line, later
# RUN apt-get update && apt-get install something-dev
