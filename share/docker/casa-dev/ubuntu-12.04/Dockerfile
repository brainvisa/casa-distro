# Dockerfile for image cati/casa-dev:ubuntu-12.04

FROM cati/casa-test:ubuntu-12.04 

# Install system dependencies

# install python and pip to get apt-mirror-updater
# in order to select an efficient debian mirror.
# (try installing up to 5 times if the default server sometimes disconnects)
RUN for trial in 1 2 3 4 5; do apt-get update && break; done \
 && for trial in 1 2 3 4 5; do DEBIAN_FRONTEND=noninteractive apt-get install -y python-setuptools && break; done \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
# RUN easy_install pip
# pip cannot be installed any longer using easy_install, the system pip
# does not work any  longer...
RUN cd /tmp && wget --no-check-certificate https://pypi.python.org/packages/c4/44/e6b8056b6c8f2bfd1445cc9990f478930d8e3459e9dbf5b8e2d2922d64d3/pip-9.0.3.tar.gz && tar xf pip-9.0.3.tar.gz && cd pip-9.0.3 && python setup.py install && hash pip && cd .. && rm -rf pip-9.0.3 pip-9.0.3.tar.gz
# pip 10 does not allow reinstalling some packages (numpy...) so we keep pip 9

# RUN pip install apt-mirror-updater
# (note: actually apt-mirror-updater does not work well on ubuntu 12.04)
# # setup best mirror in /etc/apt/sources.list
# RUN apt-mirror-updater -a

# add neurodebian repositories and install a few packages
RUN wget -O- http://neuro.debian.net/lists/precise.de-m.full | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list \
    && apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9

# WARNING: it is necessary to call apt-get install for each packages to
# avoid the 101th package issue
RUN apt-get update \
 && apt-get upgrade -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y apt-transport-https \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y cmake \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y cmake-curses-gui \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y subversion \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-software-properties \
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
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-matplotlib \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-qt4-gl \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-7-jdk \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libltdl7-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libncurses5-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y vim \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y nano \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y wget \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgtk2.0 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgtk2.0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libopenjpeg2 \
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
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libffi-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libmpich1.0-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgstreamer0.10-dev \
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
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libgstreamer-plugins-base0.10-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y libaudio-dev \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-yaml \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y zip \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y unzip \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y bash-completion \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-dbg \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y wkhtmltopdf \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-opengl \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y pax-utils \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y python-joblib \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y gedit \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y kwrite \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y kate \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y meld \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y kompare \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y kdiff3 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y gitg \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y gitk \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y spyder \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y pandoc \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
 
# # WARNING: The package repository for apt can not be added before first update
# # because it needs the apt-transport-https to be installed previously. This leed
# # to a second necessary apt update call. Moreover, it does not actually work
# # on ubuntu 12.04 because git is not recent enough (version>=1.8.2 required)
# RUN wget --no-check-certificate -O- "https://packagecloud.io/install/repositories/github/git-lfs/config_file.list?os=ubuntu&dist=precise&source=script" \
#     | sudo tee /etc/apt/sources.list.d/github_git-lfs.list \
#     && wget --no-check-certificate -O- https://packagecloud.io/github/git-lfs/gpgkey 2>/dev/null | apt-key add - \
#     && apt-get update \
#     && DEBIAN_FRONTEND=noninteractive apt-get install -y git-lfs \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# remove a few packages that will be reinstalled via pip as newer versions
RUN apt-get remove -y ipython
RUN apt-get remove -y python-scipy
RUN apt-get remove -y python-chardet
RUN apt-get remove -y python-docutils
RUN apt-get remove -y python-simplejson

# we must specify pypi URL because it has changed (was http://pypi.python.org)
RUN pip install -U -i https://pypi.org/simple 'setuptools==41.0.1'
RUN pip install -U -i https://pypi.org/simple 'pip<19.2'
RUN hash pip
RUN pip install -U 'pkgconfig<1.6'
RUN pip install -U 'cython<0.30'
RUN pip install --ignore-installed -U 'numpy<1.17'
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
RUN CPPFLAGS='-I/usr/include/mpi' pip install --no-binary=h5py 'h5py<2.9'

# ipython / jupyter
RUN pip install -U 'pyzmq<18.1'
RUN pip install -U 'ipython<6.0'
RUN pip install -U "tornado<5"
RUN pip install 'jupyter==1.0.0'
RUN pip install 'qtconsole<4.5'
RUN pip install -U 'jupyter_client<5.3'
RUN pip install -U 'scipy<1.3'
RUN pip install -U 'docutils<0.15'
# sphinx 1.7 has bugs
RUN pip install -U "sphinx<1.7"
RUN pip install -U "sphinx-gallery<0.4"
RUN pip install -U 'nbsphinx<0.4'
RUN pip install "pandoc<2.0"

# install xmltodict and other python packages
RUN pip install xmltodict
RUN pip install "python_jenkins==0.4.16"
RUN pip install 'simplejson<3.17'
RUN pip install 'nipype<1.2'
RUN pip install 'dipy<0.15'
RUN pip install -U 'nibabel<2.5'
RUN pip install 'scikit-learn<0.21'
RUN pip install -U 'dicom<0.10'
RUN pip install subprocess32
RUN pip install tqdm

RUN pip install -U 'lark-parser>=0.7,<0.8'
RUN pip install -U 'sqlalchemy<1.4'
RUN pip install -U 'xlrd<1.3'
RUN pip install -U 'xlwt<1.4'
RUN pip install -U 'jinja2<2.11'
RUN pip install 'pandas<0.25'

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
RUN echo \
'export PATH=${PATH}:/casa/brainvisa-cmake/bin\n'\
'if [ -f "${CASA_BUILD}/bin/bv_env.sh" ]; then\n'\
'    OLD_CWD=$(pwd)\n'\
'    cd ${CASA_BUILD}/bin\n'\
'    PATH=.:"$PATH"\n'\
'    . ./bv_env.sh\n'\
'    cd ${OLD_CWD}'\
'    unset OLD_CWD\n'\
'fi' > /usr/local/bin/init-casa-env

RUN sed -i 's%"$@"%. /usr/local/bin/init-casa-env\n"$@"%g' /usr/local/bin/entrypoint

# Set variable to make bv_maker use /casa/conf/bv_maker.cfg by default
ENV BRAINVISA_BVMAKER_CFG=/casa/conf/bv_maker.cfg

RUN ldconfig

# newer additions, to be placed in the other apt line, later
# RUN apt-get update && apt-get install something-dev
