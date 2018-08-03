# Dockerfile for image cati/casa-dev:ubuntu-16.04

FROM cati/casa-test:ubuntu-16.04 

# Install system dependencies
# WARNING: it is necessary to call apt-get install for each packages to 
# avoid the 101th package issue
RUN apt-get update \
 && apt-get upgrade -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y cmake \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y cmake-curses-gui \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y subversion \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y git \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qt4-dev-tools \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qt4-designer \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qt4-qmake \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qt4-qmlviewer \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qt4-qtconfig \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qt4-linguist-tools \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-sip-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-qt4-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libsigc++-2.0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y zlib1g-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y sqlite3 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libsqlite3-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libnetcdf-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libreadline-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libboost-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libblitz0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libtiff-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libjpeg-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libpng-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libmng-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y graphviz \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y graphviz-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libminc-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libdcmtk2-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqwt5-qt4-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y doxygen \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y pyro \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-paramiko \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxml2-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y gfortran \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libsvm-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-epydoc \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-sphinx \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-matplotlib \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-qt4-gl \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-8-jdk \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libltdl7-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libncurses5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y vim \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y nano \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y wget \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgtk2.0 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgtk2.0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libopenjpeg-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgdk-pixbuf2.0-common \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgdk-pixbuf2.0-0 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgdk-pixbuf2.0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y automake \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y texlive-fonts-recommended \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-dicom \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-traits \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y lftp \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y apt-utils \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y g++-4.9 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgfortran-4.9-dev \
# && DEBIAN_FRONTEND=noninteractive apt-get install -y openslide-tools \  # Needed?
# && DEBIAN_FRONTEND=noninteractive apt-get install -y libqtassistantclient4 \  # Needed?
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqtwebkit-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libblas-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y liblapack-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libffi-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libmpich-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgstreamer1.0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgstreamer-plugins-base0.10-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgstreamer-plugins-base1.0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y liborc-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxslt-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libicu-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y gdb \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y mesa-utils \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y x11proto-gl-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-setuptools \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y kdesdk-scripts \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y net-tools \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y liblapack-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libatlas-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libbz2-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libzmq-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgsl0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libjasper-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y locate \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libaudio-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-yaml \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y pandoc \
# && DEBIAN_FRONTEND=noninteractive apt-get install -y libvtk5-dev \ # later ?
 && DEBIAN_FRONTEND=noninteractive apt-get install -y gadfly \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pyqt5 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pyqt5.qtmultimedia \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pyqt5.qtopengl \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pyqt5.qtsvg \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pyqt5.qtwebkit \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pyqt5.qtsql \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pyqt5.qtwebsockets \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pyqt5.qtxmlpatterns \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-mysqldb \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-requests \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-jenkins \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y ipython3 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y ipython3-notebook \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y ipython3-qtconsole \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-matplotlib \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5.qtmultimedia \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5.qtopengl \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5.qtsvg \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5.qtwebkit \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5.qtsql \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5.qtwebsockets \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5.qtxmlpatterns \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-traits \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pydot \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-configobj \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-sip-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt4.qtsql \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt4.phonon \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt4.qtopengl \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-sphinx \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-sphinx-paramlinks \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pandas \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-xmltodict \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-xmltodict \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-fastcluster \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-mysqldb \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y pyqt5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y pyqt5-dev-tools \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqt5opengl5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqt5svg5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqt5webkit5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqt5websockets5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqt5x11extras5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqt5xmlpatterns5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqt5waylandclient5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libphonon4qt5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqwt-qt5-6 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qttools5-dev-tools \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qtmultimedia5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pyqt5.qtx11extras \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-ipython-genutils \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y cython3 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-yaml \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-requests \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-jenkins \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-opengl \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libnifti-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y x11proto-print-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y bash-completion \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y qtpositioning5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libqt5sensors5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libdouble-conversion-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgraphite2-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libharfbuzz-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libhyphen-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-subprocess32 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-keysyms1-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-randr0 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-render-util0 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-render0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-shape0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-shm0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-sync-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-util-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-xfixes0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-xkb-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-image0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-icccm4-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libxcb-render-util0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-dbg \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y wkhtmltopdf \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

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
RUN pip3 install -U 'ipython>=5.0,<6.0'
RUN pip3 install -U pandas

# WARNING: easy_install gets installed in /usr/local/bin/easy_install
# for python 3! Same for pip, we have to force installing pip for python2
# using the system easy_install (python2)
RUN /usr/bin/easy_install pip

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
RUN pip install -U pandas

# fix python command used in jupyter kernel
# note: the "official" way is to run: ipython3 kernel install, but here
# in docker it runs an interactive shell for an unknown reason.
# So we go back to manual patching
RUN sed -e 's/  "python",/  "python3",/' < /usr/local/share/jupyter/kernels/python3/kernel.json > /tmp/kernel3.json && cp /tmp/kernel3.json /usr/local/share/jupyter/kernels/python3/kernel.json

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

# install libXp, used by some external software (SPM...)
RUN cd /tmp && wget https://mirror.umd.edu/ubuntu/pool/main/libx/libxp/libxp_1.0.2.orig.tar.gz && tar xf libxp_1.0.2.orig.tar.gz && cd libXp-1.0.2 && ./configure && make -j4 && make -j4 install; cd /tmp; rm -R libxp_1.0.2.orig.tar.gz libXp-1.0.2

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
RUN chmod +x /usr/local/bin/svn

# allow attach gdb to a process
RUN echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# Install a version of brainvisa-cmake
RUN svn export https://bioproj.extra.cea.fr/neurosvn/brainvisa/development/brainvisa-cmake/branches/bug_fix $CASA_SRC/development/brainvisa-cmake/bug_fix && \
    mkdir /tmp/brainvisa-cmake  && \
    cd /tmp/brainvisa-cmake && \
    cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/bug_fix && \
    make install && cd .. && rm -r /tmp/brainvisa-cmake

# Set casa environement variables initialization
RUN echo \
'export PATH=${PATH}:/casa/brainvisa-cmake/bin\n'\
'if [ -f "${CASA_BUILD}/bin/bv_env.sh" ]; then\n'\
'    OLD_CWD=$(pwd)\n'\
'    cd ${CASA_BUILD}/bin\n'\
'    PATH=.:"$PATH"\n'\
'    . ./bv_env.sh\n'\
'    unset OLD_CWD\n'\
'fi' > /usr/local/bin/init-casa-env

RUN sed -i 's%"$@"%. /usr/local/bin/init-casa-env\n"$@"%g' /usr/local/bin/entrypoint


# Set variable to make bv_maker use /casa/conf/bv_maker.cfg by default
ENV BRAINVISA_BVMAKER_CFG=/casa/conf/bv_maker.cfg

RUN ldconfig

# newer additions, to be placed in the other apt line, later
# RUN apt-get update && apt-get install something-dev
