# Dockerfile for image cati/brainvisa-devbase:ubuntu-18.04

FROM cati/casa-test:ubuntu-18.04

# Install system dependencies
RUN apt-get update && apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    cmake \
    cmake-curses-gui \
    subversion \
    git \
    python-sip-dev \
    libsigc++-2.0-dev \
    zlib1g-dev \
    sqlite3 \
    libsqlite3-dev \
    libnetcdf-dev \
    libreadline-dev \
    libboost-dev \
    libtiff-dev \
    libjpeg-dev \
    libpng-dev \
    libmng-dev \
    graphviz \
    graphviz-dev \
    libminc-dev \
    libdcmtk2-dev \
    doxygen \
    pyro \
    python-paramiko \
    libxml2-dev \
    gfortran \
    libsvm-dev \
    python-epydoc \
    python-sphinx \
    python-matplotlib \
    openjdk-8-jdk \
    libltdl7-dev \
    libncurses5-dev \
    vim \
    nano \
    wget \
    libgtk2.0 \
    libgtk2.0-dev \
    libjpeg-turbo8-dev \
    libgdk-pixbuf2.0-common \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    automake \
    texlive-fonts-recommended \
    python-dicom \
    python-traits \
    lftp \
    apt-utils \
    libblas-dev \
    liblapack-dev \
    libffi-dev \
    libmpich-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    liborc-0.4-dev \
    libxslt1-dev \
    libicu-dev \
    gdb \
    mesa-utils \
    x11proto-gl-dev \
    python-setuptools \
    kdesdk-scripts \
    net-tools \
    liblapack-dev \
    libbz2-dev \
    libzmq3-dev \
    libgsl-dev \
#     libjasper-dev
    locate \
    libaudio-dev \
    python-yaml \
    pandoc \
    gadfly \
    python-pyqt5 \
    python-pyqt5.qtmultimedia \
    python-pyqt5.qtopengl \
    python-pyqt5.qtsvg \
    python-pyqt5.qtwebkit \
    python-pyqt5.qtsql \
    python-pyqt5.qtwebsockets \
    python-pyqt5.qtxmlpatterns \
    python-mysqldb \
    python-requests \
    python-pip \
#     python-jenkins
    ipython3 \
    ipython3-qtconsole \
    python3-matplotlib \
    python3-pyqt5 \
    python3-pyqt5.qtmultimedia \
    python3-pyqt5.qtopengl \
    python3-pyqt5.qtsvg \
    python3-pyqt5.qtwebkit \
    python3-pyqt5.qtsql \
    python3-pyqt5.qtwebsockets \
    python3-pyqt5.qtxmlpatterns \
    python3-traits \
    python3-pip \
    python3-pydot \
    python3-configobj \
    python3-sip-dev \
    python3-sphinx \
    python3-sphinx-paramlinks \
    python3-pandas \
    python-xmltodict \
    python3-xmltodict \
    python3-fastcluster \
    python3-mysqldb \
    pyqt5-dev \
    pyqt5-dev-tools \
    libqt5opengl5-dev \
    libqt5svg5-dev \
    libqt5webkit5-dev \
    libqt5websockets5-dev \
    libqt5x11extras5-dev \
    libqt5xmlpatterns5-dev \
    libqt5waylandclient5-dev \
    libphonon4qt5-dev \
    qttools5-dev \
    libqwt-qt5-6 \
    qttools5-dev-tools \
    qtmultimedia5-dev \
    python3-pyqt5.qtx11extras \
    python3-ipython-genutils \
    cython3 \
    python3-yaml \
    python3-requests \
    python3-jenkins \
    python3-opengl \
    libnifti-dev \
    x11proto-print-dev \
    bash-completion \
    unzip \
    libopenjp2-7-dev \
    clang \
    qt5-default \
    ghostscript \
    libqwt-qt5-dev \
    qtpositioning5-dev \
    libqt5sensors5-dev \
    libqt5webchannel5-dev \
    libdouble-conversion-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN cd /tmp \
  && wget --no-check-certificate https://github.com/blitzpp/blitz/archive/1.0.1.zip && unzip 1.0.1.zip && cd blitz-1.0.1 \
  && ./configure \
  && make -j4 \
  && make -j4 install \
  && cd .. \
  && rm -rf 1.0.1.zip blitz-1.0.1

# pip3 modules should be installed first, then some commands
# (/usr/local/bin/jupyter* for instance) will be replaced by python2
# equivalents when installed by pip2. jupyter modules especially handle
# these conflicts very badly.
RUN pip3 install -U numpy
RUN pip3 install -U scipy
RUN pip3 install nipype
RUN pip3 install jupyter
RUN pip3 install nbsphinx
RUN pip3 install cython
RUN pip3 install dipy
RUN pip3 install -U nibabel
RUN pip3 install sklearn

# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
RUN pip install -U pkgconfig
RUN pip install -U cython
RUN pip install -U numpy
RUN pip install -U setuptools
RUN CPPFLAGS='-I/usr/include/mpi' pip install --no-binary=h5py h5py

# ipython / jupyter
RUN pip install -U 'ipython>=5.0,<6.0'
RUN pip install jupyter
RUN pip install -U zmq
RUN pip install -U scipy
RUN pip install -U nbsphinx
# sphinx 1.7 has bugs
RUN pip install -U "sphinx>=1.5,<1.7"

RUN pip install nipype
RUN pip install dipy
RUN pip install -U nibabel
RUN pip install sklearn
RUN pip install -U pyparsing
RUN pip install -U pydot
RUN pip install "python_jenkins==0.4.16"

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

# RUN cd /tmp && git clone https://git01.codeplex.com/jxrlib && cd jxrlib && DIR_INSTALL=/usr/local SHARED=1 make -j4 install && cd /tmp && rm -R jxrlib
RUN cd /tmp && wget https://codeplexarchive.blob.core.windows.net/archive/projects/jxrlib/jxrlib.zip && mkdir jxrlib && cd jxrlib && unzip ../jxrlib.zip; cd sourceCode/jxrlib && DIR_INSTALL=/usr/local SHARED=1 make -j4 install && cd /tmp && rm -R jxrlib jxrlib.zip

RUN cd /tmp && git clone https://github.com/MIRCen/openslide.git && cd openslide && libtoolize --force && aclocal && autoheader && automake --force-missing --add-missing && autoconf && ./configure && make -j4 install && cd /tmp && rm -R openslide

# install a version of netcdf with fewer dependencies
COPY build_netcdf.sh /tmp/build_netcdf.sh
RUN bash /tmp/build_netcdf.sh && rm /tmp/build_netcdf.sh

# install libXp, used by some external software (SPM...)
RUN cd /tmp && wget https://mirror.umd.edu/ubuntu/pool/main/libx/libxp/libxp_1.0.2.orig.tar.gz && tar xf libxp_1.0.2.orig.tar.gz && cd libXp-1.0.2 && ./configure && make -j4 && make -j4 install; cd /tmp; rm -R libxp_1.0.2.orig.tar.gz libXp-1.0.2

# cmake does not work with clang whenever Qt5 is invoked.
# workaround here:
# https://stackoverflow.com/questions/38027292/configure-a-qt5-5-7-application-for-android-with-cmake/40256862#40256862
RUN sed 's/^\(set_property.*INTERFACE_COMPILE_FEATURES.*\)$/#\ \1/' < /usr/lib/x86_64-linux-gnu/cmake/Qt5Core/Qt5CoreConfigExtras.cmake > /tmp/Qt5CoreConfigExtras.cmake && cp -f /tmp/Qt5CoreConfigExtras.cmake /usr/lib/x86_64-linux-gnu/cmake/Qt5Core/Qt5CoreConfigExtras.cmake

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

RUN ldconfig

# newer additions, to be placed in the other apt line, later
# RUN apt-get update && apt-get install something-dev
