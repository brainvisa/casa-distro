# Dockerfile for image cati/casa-dev:windows-7-64

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
ENV CASA_SYS=/casa/sys

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
    bash-completion \
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

# create casa directories for singularity compatibility  
RUN mkdir -p $CASA_CONF \
             $CASA_SRC \
             $CASA_CUSTOM_SRC \
             $CASA_BUILD \
             $CASA_CUSTOM_BUILD \
             $CASA_SYS

RUN chmod 777 $CASA_CONF \
              $CASA_SRC \
              $CASA_CUSTOM_SRC \
              $CASA_BUILD \
              $CASA_CUSTOM_BUILD \
              $CASA_SYS
             
COPY svn.secret $CASA_CONF/svn.secret
COPY svn /usr/local/bin/svn
RUN chmod +x /usr/local/bin/svn

# allow attach gdb to a process
RUN echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# Install a version of brainvisa-cmake
RUN svn export https://bioproj.extra.cea.fr/neurosvn/brainvisa/development/brainvisa-cmake/branches/bug_fix $CASA_SRC/development/brainvisa-cmake/bug_fix && \
    mkdir /tmp/brainvisa-cmake  && \
    cd /tmp/brainvisa-cmake && \
    cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/bug_fix && \
    make install && cd .. && rm -r /tmp/brainvisa-cmake

# Set PATH to have bv_env_host being either the one of the build directory (/casa/build)
# or the one in the image (/casa/brainvisa-cmake)
ENV PATH=${PATH}:$CASA_BUILD/bin:/casa/brainvisa-cmake/bin

# Set variable to make bv_maker use /casa/conf/bv_maker.cfg by default
ENV BRAINVISA_BVMAKER_CFG=$CASA_CONF/bv_maker.cfg

# Generate workflow initilialization script
RUN echo "#!/usr/bin/env bash \n" \
         "/usr/local/bin/init-wine " \
         '&& CASA_DEPS_WIN="$(winepath -w ${CASA_DEPS})" ' \
         '&& CASA_DEPS_WIN="${CASA_DEPS_WIN//\\/\\\\}" ' \
         "&& wineserver -k -w " \
         "&& /casa/brainvisa-cmake/bin/bv_wine_regedit " \
         "--registry-action 'prepend' " \
         '--value-path "HKLM\\\\System\\\\CurrentControlSet\\\\Control\\\\Session Manager\\\\Environment\\\\PATH" ' \
         '--value "${CASA_DEPS_WIN}\\\\bin" ' \ 
         "&& /casa/brainvisa-cmake/bin/bv_wine_regedit " \         
         '--value-path "HKLM\\\\System\\\\CurrentControlSet\\\\Control\\\\Session Manager\\\\Environment\\\\PYTHONHOME" ' \
         '--value "${CASA_DEPS_WIN}\\python" ' \
         "&& /casa/brainvisa-cmake/bin/bv_wine_regedit " \
         "--registry-action 'prepend' " \         
         '--value-path "HKLM\\\\System\\\\CurrentControlSet\\\\Control\\\\Session Manager\\\\Environment\\\\QT_PLUGIN_PATH" ' \
         '--value "${CASA_DEPS_WIN}\\qt\\plugins"' > /usr/local/bin/init-workflow

RUN chmod 777 /usr/local/bin/init-workflow

# newer additions, to be placed in the other apt line, later
# RUN apt-get update && apt-get install something-dev
