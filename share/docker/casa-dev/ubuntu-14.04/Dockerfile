# Dockerfile for image cati/brainvisa-devbase:ubuntu-12.04

FROM cati/casa-test:ubuntu-14.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    cmake-curses-gui \
    subversion \
    git \
    qt4-dev-tools \
    qt4-designer \
    qt4-qmake \
    qt4-qmlviewer \
    qt4-qtconfig \
    qt4-linguist-tools \
    python-sip-dev \
    python-qt4-dev \
    libsigc++-2.0-dev \
    zlib1g-dev \
    sqlite3 \
    libsqlite3-dev \
    libnetcdf-dev \
    libreadline-dev \
    libboost-dev \
    libblitz0-dev \
    libtiff-dev \
    libjpeg-dev \
    libpng-dev \
    libmng-dev \
    graphviz \
    graphviz-dev \
    libminc-dev \
    libdcmtk2-dev \
    libqwt5-qt4-dev \
    doxygen \
    pyro \
    python-paramiko \
    libxml2-dev \
    gfortran \
    libsvm-dev \
    python-sphinx \
    python-matplotlib \
    python-qt4-gl \
    openjdk-7-jdk \
    libltdl7-dev \
    libncurses5-dev \
    vim \
    nano \
    wget \
    libgtk2.0 \
    libgtk2.0-dev \
    libopenjpeg2 \
    libopenjpeg-dev \
    libgdk-pixbuf2.0-common \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    automake \
    texlive-fonts-recommended \
    python-dicom \
    python-traits \
    lftp \
    apt-utils \
    libffi-dev \
    libmpich-dev \
    libgstreamer0.10-dev \
    liborc-dev \
    libxslt-dev \
    libicu-dev \
    gdb \
    mesa-utils \
    x11proto-gl-dev \
    python-setuptools \
    kdesdk-scripts \
    net-tools \
    liblapack-dev \
    libatlas-dev \
    libbz2-dev \
    libzmq-dev \
    libgsl0-dev \
    libjasper-dev \
    locate \
    libgstreamer-plugins-base0.10-dev \
    libaudio-dev \
    python-yaml \
    pandoc \
    zip \
    unzip \
    libssl-dev \
#     libvtk5-dev \ # later ?
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# RUN easy_install pip
# pip cannot be installed any longer using easy_install, the system pip 
# does not work any  longer...
RUN cd /tmp && wget https://pypi.python.org/packages/c4/44/e6b8056b6c8f2bfd1445cc9990f478930d8e3459e9dbf5b8e2d2922d64d3/pip-9.0.3.tar.gz#md5=b15b33f9aad61f88d0f8c866d16c55d8 && tar xf pip-9.0.3.tar.gz && cd pip-9.0.3 && python setup.py install && hash pip && pip install -U pip && cd .. && rm -rf pip-9.0.3 pip-9.0.3.tar.gz
# ipython / jupyter
RUN pip install -U 'ipython>=5.0,<6.0'
RUN pip install -U "tornado>=4,<5"
RUN pip install jupyter
RUN pip install -U zmq
RUN pip install -U numpy
RUN pip install -U scipy
RUN pip install -U docutils
RUN pip install -U nbsphinx
# sphinx 1.7 has bugs
RUN pip install -U "sphinx>=1.5,<1.7"
RUN pip install jupyter_client

# install xmltodict and other python packages
RUN pip install xmltodict
RUN pip install python_jenkins
RUN pip install nipype

# install Pycluster
RUN cd /tmp \
  && wget http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.52.tar.gz \
  && tar xfz Pycluster-1.52.tar.gz \
  && cd Pycluster-1.52 \
  && python setup.py build \
  && python setup.py install \
  && cd .. \
  && \rm -r Pycluster-1.52 Pycluster-1.52.tar.gz

# Install Qt Installer Framework (prebuilt on Mandriva 2008)
RUN cd /tmp \
  && wget http://brainvisa.info/static/qt_installer-1.6.tar.gz \
  && cd /usr/local \
  && tar xfz /tmp/qt_installer-1.6.tar.gz \
  && ln -s qt_installer-1.6 qt_installer \
  && cd /usr/local/bin \
  && ln -s ../qt_installer/bin/* . \
  && rm /tmp/qt_installer-1.6.tar.gz

# COPY qt_installer_script /tmp/qt_installer_script
# RUN wget -q http://download.qt.io/official_releases/qt-installer- framework/2.0.3/QtInstallerFramework-linux-x64.run -O /tmp/QtInstallerFramework-linux-x64.run && \
#    chmod +x /tmp/QtInstallerFramework-linux-x64.run && \
#    xvfb-run /tmp/QtInstallerFramework-linux-x64.run --script /tmp/qt_installer_script && \
#    ln -s /usr/local/qt-installer/bin/* /usr/local/bin/ && \
#    rm /tmp/QtInstallerFramework-linux-x64.run /tmp/qt_installer_script

# RUN cd /tmp && git clone https://git01.codeplex.com/jxrlib && cd jxrlib && DIR_INSTALL=/usr/local SHARED=1 make -j4 install && cd /tmp && rm -R jxrlib
RUN cd /tmp && wget https://codeplexarchive.blob.core.windows.net/archive/projects/jxrlib/jxrlib.zip && mkdir jxrlib && cd jxrlib && unzip ../jxrlib.zip; cd sourceCode/jxrlib && DIR_INSTALL=/usr/local SHARED=1 make -j4 install && cd /tmp && rm -R jxrlib jxrlib.zip
RUN cd /tmp && git clone https://github.com/MIRCen/openslide.git && cd openslide && libtoolize --force && aclocal && autoheader && automake --force-missing --add-missing && autoconf && ./configure && make -j4 install && cd /tmp && rm -R openslide

# install a version of netcdf with fewer dependencies
COPY build_netcdf.sh /tmp/build_netcdf.sh
RUN bash /tmp/build_netcdf.sh && rm /tmp/build_netcdf.sh

# install a newer version of boost
COPY build_boost.sh /tmp/build_boost.sh
RUN bash /tmp/build_boost.sh && rm /tmp/build_boost.sh

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
ENV PATH=${PATH}:/casa/build/bin:/casa/brainvisa-cmake/bin

# Set variable to make bv_maker use /casa/conf/bv_maker.cfg by default
ENV BRAINVISA_BVMAKER_CFG=/casa/conf/bv_maker.cfg

# newer additions, to be placed in the other apt line, later
# RUN apt-get update && apt-get install something-dev
