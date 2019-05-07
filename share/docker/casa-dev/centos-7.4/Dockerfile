# Dockerfile for image cati/casa-dev:centos-7.4

FROM cati/casa-test:centos-7.4 

# Install system dependencies
RUN wget http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
 && rpm -ivh epel-release-latest-7.noarch.rpm \
 && \rm -f epel-release-latest-7.noarch.rpm \
 && yum -y groupinstall "Development Tools" \
 && yum -y install \
    cmake \
    cmake-gui \
    git \
    qt-devel \
    qt-config \
    qt-x11 \
    qt-assistant \
    qt-creator \
    qtwebkit-devel \
    phonon-devel \
    qwt-devel \
    sip-devel \
    PyQt4-devel \
    PyQt4-webkit-devel \
    libsigc++20-devel \
    zlib-devel \
    sqlite-devel \
    readline-devel \
    boost-devel \
    libtiff-devel \
    openjpeg-devel \
    turbojpeg-devel \
    libpng-devel \
    libmng-devel \
    libwebp-devel \
    agg-devel \
    hdf5-devel \
    netcdf-devel \
    libsvm-devel \
    czmq-devel \
    openssl-devel \
    graphviz \
    graphviz-devel \
    python-paramiko \
    libxml2-devel \
    python-sphinx \
    python-sqlalchemy \
    python-lark-parser \
    java-1.7.0-openjdk \
    libtool-ltdl-devel \
    ncurses-devel \
    vim-minimal \
    nano \
    wget \
    gtk2 \
    gtk2-devel \
    gdk-pixbuf2 \
    gdk-pixbuf2-devel \
    automake \
    texlive-fontspec \
    texlive-fontware \
    texlive-fontwrap \
    texlive-fontmisc \
    python-setuptools \
    python-subprocess32 \
    lftp \
    libffi-devel \
    gstreamer-devel \
    orc-devel \
    libxslt-devel \
    libicu-devel \
    gdb \
    mesa-libOSMesa-devel \
    xorg-x11-proto-devel \
    net-tools \
    lapack-devel \
    atlas-devel \
    bzip2-devel \
    gsl-devel \
    jasper-devel \
    pandoc \
    mlocate \
    gstreamer-plugins-base-devel \
    gstreamer1-plugins-base-devel \
    audiofile-devel \
    openpgm-devel \
    libyaml-devel \
    jbigkit-devel \
    PyYAML \
    zip \
    unzip \
    kdesdk-scripts \
    bash-completion \
    perl-devel \
    perl-CPAN \
    pax-utils \
    python36 \
    python36-devel \
    python36-setuptools \
    vim \
    gedit \
    kwrite \
    kate \
    meld \
    kompare \
    kdiff3 \
    gitg \
    gitk \
    git-lfs \
 && yum clean all

# spyder cannot be installed because it needs "python-rope" which doesn't
# exist.

ENV CEA_MIRROR_URL=ftp://ftp.cea.fr/pub/dsv/anatomist/3rdparty/1.0.0/centos-7.4

# install dcmtk
COPY build_dcmtk.sh /tmp/build_dcmtk.sh
RUN bash -c "DCMTK_MIRROR_URL=${CEA_MIRROR_URL}/sources /tmp/build_dcmtk.sh" \
    && rm /tmp/build_dcmtk.sh

# install minc
COPY build_minc.sh /tmp/build_minc.sh
RUN bash -c "MINC_MIRROR_URL=${CEA_MIRROR_URL}/sources /tmp/build_minc.sh" \
    && rm /tmp/build_minc.sh

# install blitz
COPY build_blitz.sh /tmp/build_blitz.sh
RUN bash -c "BLITZ_MIRROR_URL=${CEA_MIRROR_URL}/sources /tmp/build_blitz.sh" \
    && rm /tmp/build_blitz.sh

# install doxygen
COPY build_doxygen.sh /tmp/build_doxygen.sh
RUN bash -c "DOXYGEN_MIRROR_URL=${CEA_MIRROR_URL}/sources /tmp/build_doxygen.sh" \
    && rm /tmp/build_doxygen.sh
 
# install git
COPY build_git.sh /tmp/build_git.sh
RUN bash -c "GIT_MIRROR_URL=${CEA_MIRROR_URL}/sources /tmp/build_git.sh" \
    && rm /tmp/build_git.sh

# install openmpi
COPY build_openmpi.sh /tmp/build_openmpi.sh
RUN bash -c "OPENMPI_MIRROR_URL=${CEA_MIRROR_URL}/sources /tmp/build_openmpi.sh" \
    && rm /tmp/build_openmpi.sh

    
#RUN easy_install pip
# pip cannot be installed any longer using easy_install, the system pip 
# does not work any  longer...
RUN cd /tmp && wget https://pypi.python.org/packages/c4/44/e6b8056b6c8f2bfd1445cc9990f478930d8e3459e9dbf5b8e2d2922d64d3/pip-9.0.3.tar.gz#md5=b15b33f9aad61f88d0f8c866d16c55d8 && tar xf pip-9.0.3.tar.gz && cd pip-9.0.3 && python setup.py install && hash pip && cd .. && rm -rf pip-9.0.3 pip-9.0.3.tar.gz
RUN pip --version

# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
RUN pip install -U pkgconfig
RUN pip install -U cython
RUN pip install -U "numpy<1.17"
RUN pip install -U setuptools
RUN CPPFLAGS='-I/usr/include/mpi' pip install --no-binary=h5py h5py

# ipython / jupyter
RUN pip install -U 'ipython<6.0'
RUN pip install -U "tornado>=4,<5"
RUN pip install jupyter
RUN pip install -U zmq
RUN pip install -U 'scipy<1.3'
#RUN pip install -U docutils
RUN pip install -U nbsphinx
RUN pip install -U traits
RUN pip install -U dicom
RUN pip install -U pydicom
RUN pip install -U pyro
# sphinx 1.7 has bugs
RUN pip install -U "sphinx>=1.5,<1.7"
RUN pip install "sphinx-gallery<0.4"
RUN pip install jupyter_client
RUN pip install 'matplotlib<3.1'

# install xmltodict and other python packages
RUN pip install xmltodict
RUN pip install "python_jenkins==0.4.16"
RUN pip install nipype
RUN pip install 'dipy<0.15'
RUN pip install -U nibabel
RUN pip install "scikit-learn==0.19.1"
RUN pip install -U pyparsing
RUN pip install -U pydot
RUN pip install mpi4py

RUN pip install -U 'lark-parser<0.7'
RUN pip install -U xlrd
RUN pip install -U xlwt

# # install pip3 and pytorch in python3
# RUN mkdir -p /usr/local/lib/python3.6/site-packages
# RUN easy_install-3.6 pip
# RUN pip3 install torch


# install Pycluster
# http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.52.tar.gz
RUN cd /tmp \
  && wget ${CEA_MIRROR_URL}/sources/Pycluster-1.52.tar.gz \
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

# Install jxrlib + openslide
#https://codeplexarchive.blob.core.windows.net/archive/projects/jxrlib/jxrlib.zip
RUN cd /tmp \
    && wget ${CEA_MIRROR_URL}/sources/jxrlib-1.1.zip -O jxrlib.zip && mkdir jxrlib && cd jxrlib && unzip ../jxrlib.zip && DIR_INSTALL=/usr/local SHARED=1 make -j4 install && cd /tmp && rm -R jxrlib jxrlib.zip
RUN cd /tmp && git clone https://github.com/MIRCen/openslide.git && cd openslide && libtoolize --force && aclocal && autoheader && automake --force-missing --add-missing && autoconf && ./configure && make -j4 install && cd /tmp && rm -R openslide

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

# create casa directories for singularity compatibility  
RUN mkdir -p $CASA_CONF \
             $CASA_SRC \
             $CASA_CUSTOM_SRC \
             $CASA_BUILD \
             $CASA_CUSTOM_BUILD

RUN chmod 777 $CASA_CONF \
              $CASA_SRC \
              $CASA_CUSTOM_SRC \
              $CASA_BUILD \
              $CASA_CUSTOM_BUILD
              
COPY svn.secret $CASA_CONF/svn.secret
COPY svn /usr/local/bin/svn
COPY askpass-bioproj.sh /usr/local/bin/askpass-bioproj.sh
RUN chmod +x /usr/local/bin/svn /usr/local/bin/askpass-bioproj.sh
RUN git config --system core.askPass /usr/local/bin/askpass-bioproj.sh

# allow attach gdb to a process
RUN echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# Install a version of brainvisa-cmake
RUN git clone https://github.com/brainvisa/brainvisa-cmake.git $CASA_SRC/development/brainvisa-cmake/master && \
    mkdir /tmp/brainvisa-cmake  && \
    cd /tmp/brainvisa-cmake && \
    cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/master && \
    make install && cd .. && rm -r /tmp/brainvisa-cmake

# Set casa environement variables initialization
RUN echo -e \
'export PATH=${PATH}:/casa/brainvisa-cmake/bin\n'\
'if [ -f "${CASA_BUILD}/bin/bv_env.sh" ]; then\n'\
'    . ${CASA_BUILD}/bin/bv_env.sh ${CASA_BUILD}\n'\
'fi' > /usr/local/bin/init-casa-env

RUN sed -i 's%"$@"%. /usr/local/bin/init-casa-env\n"$@"%g' /usr/local/bin/entrypoint

# Set variable to make bv_maker use /casa/conf/bv_maker.cfg by default
ENV BRAINVISA_BVMAKER_CFG=/casa/conf/bv_maker.cfg

# newer additions, to be placed in the other yum line, later
# RUN yum -y install something-dev
