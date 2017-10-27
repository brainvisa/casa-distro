# Dockerfile for image cati/brainvisa-devbase:ubuntu-16.04

FROM cati/casa-test:ubuntu-16.04 

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
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
    python-epydoc \
    python-sphinx \
    python-matplotlib \
    python-qt4-gl \
    openjdk-8-jdk \
    libltdl7-dev \
    libncurses5-dev \
    vim \
    nano \
    wget \
    libgtk2.0 \
    libgtk2.0-dev \
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
    g++-4.9 \
    libgfortran-4.9-dev \
#    openslide-tools \  # Needed?
#    libqtassistantclient4 \  # Needed?
    libqtwebkit-dev \
    libblas-dev \
    liblapack-dev \
    libffi-dev \
    libmpich-dev \
    libgstreamer1.0-dev \
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
#     libvtk5-dev \ # later ?
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# ipython / jupyter
RUN easy_install pip
RUN pip install -U 'ipython>=5.0,<6.0'
RUN pip install jupyter
RUN pip install -U zmq
RUN pip install -U numpy
RUN pip install -U scipy

# install xmltodict and other python packages
RUN pip install xmltodict
RUN pip install python_jenkins

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

RUN cd /tmp && git clone https://git01.codeplex.com/jxrlib && cd jxrlib && DIR_INSTALL=/usr/local SHARED=1 make -j4 install && cd /tmp && rm -R jxrlib
RUN cd /tmp && git clone https://github.com/MIRCen/openslide.git && cd openslide && libtoolize --force && aclocal && autoheader && automake --force-missing --add-missing && autoconf && ./configure && make -j4 install && cd /tmp && rm -R openslide

# install a version of netcdf with fewer dependencies
COPY build_netcdf.sh /tmp/build_netcdf.sh
RUN bash /tmp/build_netcdf.sh && rm /tmp/build_netcdf.sh
# RUN cd /tmp \
#   && wget http://brainvisa.info/static/netcdf-4.1.1-ubuntu-12.04.tar.gz \
#   && cd /usr/local \
#   && tar xfz /tmp/netcdf-4.1.1-ubuntu-12.04.tar.gz \
#   && ln -s netcdf-4.1.1 netcdf \
#   && cd lib \
#   && ln -s ../netcdf/lib/lib* . \
#   && cd pkgconfig \
#   && ln -s ../../netcdf/lib/pkgconfig/*.pc . \
#   && cd ../../bin \
#   && ln -s ../netcdf/bin/* . \
#   && rm /tmp/netcdf-4.1.1-ubuntu-12.04.tar.gz

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

# newer additions, to be placed in the other apt line, later
# RUN apt-get update && apt-get install something-dev
