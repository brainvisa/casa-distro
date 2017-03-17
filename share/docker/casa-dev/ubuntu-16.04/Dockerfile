# Dockerfile for image cati/brainvisa-devbase:ubuntu-16.04

FROM cati/casa-test:ubuntu-16.04 

USER root

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    build-essential \
    ipython \
    cmake \
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
    python-numpy \
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
    python-six \
    libgtk2.0 \
    libgtk2.0-dev \
    libopenjpeg-dev \
    libgdk-pixbuf2.0-common \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    automake \
    texlive-fonts-recommended \
    python-scipy \
    python-dicom \
    python-traits \
    lftp \
    apt-utils \
#    python-pip \ # Needed ?
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
  && apt-get clean

# delete all the apt list files since they're big and get stale quickly
RUN rm -rf /var/lib/apt/lists/*

# Install Qt Installer Framework
COPY qt_installer_script /tmp/qt_installer_script
RUN wget -q http://download.qt.io/official_releases/qt-installer-framework/2.0.3/QtInstallerFramework-linux-x64.run -O /tmp/QtInstallerFramework-linux-x64.run && \
    chmod +x /tmp/QtInstallerFramework-linux-x64.run && \
    xvfb-run /tmp/QtInstallerFramework-linux-x64.run --script /tmp/qt_installer_script && \
    ln -s /usr/local/qt-installer/bin/* /usr/local/bin/ && \
    rm /tmp/QtInstallerFramework-linux-x64.run /tmp/qt_installer_script

RUN cd /tmp && git clone https://git01.codeplex.com/jxrlib && cd jxrlib && DIR_INSTALL=/usr/local SHARED=1 make -j4 install && cd /tmp && rm -R jxrlib

# TODO: OpenSlide does not compile due to incompatibility in GLIB version
#RUN cd /tmp && git clone https://github.com/MIRCen/openslide.git && cd openslide && libtoolize --force && aclocal && autoheader && automake --force-missing --add-missing && autoconf && ./configure && make -j4 install && cd /tmp && rm -R openslide

USER brainvisa
