# Install system dependencies for image cati/casa-dev:ubuntu-16.04

set -e # stop the script on error

set -x # display command before running them
if [ `id -u` -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

. /casa/environment.sh

# add neurodebian repositories and install a few packages
$SUDO wget -O- http://neuro.debian.net/lists/xenial.de-m.full | $SUDO tee /etc/apt/sources.list.d/neurodebian.sources.list
$SUDO apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9

# WARNING: it is necessary to call apt-get install for each package to
# avoid the 101th package issue
$SUDO apt-get update
$SUDO apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y build-essential
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y cmake
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y cmake-curses-gui
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y subversion
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y git
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-dev-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-designer
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-qmake
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-qmlviewer
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-qtconfig
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt4-linguist-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sip-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-qt4-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsigc++-2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y zlib1g-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y sqlite3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsqlite3-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnetcdf-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libreadline-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libblitz0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtiff-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjpeg-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpng-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmng-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y graphviz
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y graphviz-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libminc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdcmtk2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqwt5-qt4-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y doxygen
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyro
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-paramiko
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxml2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gfortran
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsvm-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-epydoc
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-matplotlib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-qt4-gl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sphinx
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sqlalchemy
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openjdk-8-jdk
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libltdl7-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libncurses5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y vim
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y nano
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y wget
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgtk2.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgtk2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenjpeg-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-common
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y automake
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y texlive-fonts-recommended
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-dicom
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-traits
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y lftp
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y apt-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y g++-4.9
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgfortran-4.9-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqtwebkit-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libblas-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liblapack-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libffi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmpich-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgstreamer1.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgstreamer-plugins-base0.10-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgstreamer-plugins-base1.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liborc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxslt-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libicu-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gdb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mesa-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y x11proto-gl-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-setuptools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y kdesdk-scripts
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y net-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liblapack-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libatlas-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libbz2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libzmq-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgsl0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjasper-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y locate
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libaudio-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-yaml
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pandoc
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gadfly
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtmultimedia
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtopengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtsvg
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtwebkit
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtsql
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtwebsockets
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyqt5.qtxmlpatterns
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-mysqldb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-requests
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-jenkins
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y ipython3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y ipython3-notebook
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y ipython3-qtconsole
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-matplotlib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtmultimedia
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtopengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtsvg
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtwebkit
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtsql
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtwebsockets
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtxmlpatterns
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-traits
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pip
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pydot
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-configobj
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sip-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt4.qtsql
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt4.phonon
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt4.qtopengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sphinx
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sphinx-paramlinks
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pandas
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-xmltodict
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-xmltodict
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-fastcluster
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-mysqldb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sqlalchemy
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyqt5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyqt5-dev-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5opengl5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5svg5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5webkit5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5websockets5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5x11extras5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5xmlpatterns5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5waylandclient5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libphonon4qt5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqwt-qt5-6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qttools5-dev-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qtmultimedia5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtx11extras
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-ipython-genutils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y cython3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-yaml
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-requests
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-jenkins
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnifti-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y x11proto-print-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y bash-completion
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qtpositioning5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5sensors5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdouble-conversion-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgraphite2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libharfbuzz-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhyphen-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-subprocess32
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-keysyms1-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-randr0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-render-util0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-render0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-shape0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-shm0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-sync-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-util-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-xfixes0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-xkb-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-image0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-icccm4-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-render-util0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-dbg
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y wkhtmltopdf
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-joblib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-tqdm
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-joblib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-tqdm
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y comerr-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y i965-va-driver
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y krb5-multidev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libaacs0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libarmadillo6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libarpack2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavcodec-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavcodec-ffmpeg56
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavformat-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavformat-ffmpeg56
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavutil-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavutil-ffmpeg54
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libbdplus0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libbluray1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-all-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-atomic-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-atomic1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-atomic1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-chrono-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-chrono1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-chrono1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-context-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-context1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-context1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-coroutine-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-coroutine1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-coroutine1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-date-time-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-date-time1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-date-time1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-exception-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-exception1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-filesystem-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-filesystem1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-graph-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-graph-parallel-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-graph-parallel1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-graph-parallel1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-graph1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-graph1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-iostreams-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-iostreams1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-iostreams1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-locale-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-locale1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-locale1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-log-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-log1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-log1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-math-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-math1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-math1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-mpi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-mpi-python-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-mpi-python1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-mpi-python1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-mpi1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-mpi1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-program-options-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-program-options1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-program-options1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-python-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-python1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-python1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-random-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-random1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-random1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-regex-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-regex1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-regex1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-serialization-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-serialization1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-serialization1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-signals-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-signals1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-signals1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-system-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-system1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-test-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-test1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-test1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-thread-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-thread1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-thread1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-timer-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-timer1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-timer1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-tools-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-wave-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-wave1.58-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-wave1.58.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost1.58-tools-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libcrystalhd3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdap-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdap17v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdapclient6v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdapserver7v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libeigen3-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libepsilon1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libflann-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libflann1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libfreexl1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdal-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdal1i
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgeos-3.5.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgeos-c1v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgeos-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgif-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgl2ps-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgl2ps0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgme0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgsm1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgssrpc4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhdf4-0-alt
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhdf4-alt-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhwloc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libibverbs-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libibverbs1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjsoncpp-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkadm5clnt-mit9
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkadm5srv-mit9
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkdb5-8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmlbase1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmldom1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmlengine1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libminizip1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmodplug1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmp3lame0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmysqlclient-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnetcdf-c++4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnetcdf-cxx-legacy-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnuma-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libodbc1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libogdi3.2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libogg-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenjp2-7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenmpi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenmpi1.10
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenni-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenni-sensor-pointclouds0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenni0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-apps1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-common1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-features1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-filters1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-io1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-kdtree1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-keypoints1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-octree1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-outofcore1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-people1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-recognition1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-registration1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-sample-consensus1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-search1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-segmentation1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-surface1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-tracking1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-visualization1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl1.7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpq-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpq5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libproj9
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqhull-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqhull7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libschroedinger-1.0-0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libshine3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsoxr0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libspatialite-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libspatialite7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libssh-gcrypt-4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsuperlu4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libswresample-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libswresample-ffmpeg1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libswscale-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libswscale-ffmpeg3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtheora-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtinyxml2.6.2v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtwolame0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liburiparser1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libusb-1.0-0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libva1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6-java
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6-qt-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6.2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6.2-qt
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libwebp-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libwebpdemux1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libx264-148
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libx265-79
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxdmf-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxdmf2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxerces-c-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxerces-c3.1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxss-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxvidcore4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libzvbi-common
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libzvbi0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mesa-va-drivers
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mpi-default-bin
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mpi-default-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y odbcinst
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y odbcinst1debian2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openmpi-bin
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openmpi-common
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openni-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y proj-bin
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y proj-data
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-attr
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-autobahn
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-concurrent.futures
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-mpi4py
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-msgpack
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pam
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyasn1-modules
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-serial
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-service-identity
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-snappy
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-trollius
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-twisted
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-twisted-bin
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-twisted-core
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-txaio
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-vtk6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-zope.interface
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qttools5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qttools5-private-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tcl-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tcl-vtk6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tcl8.6-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tk-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tk8.6-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y unixodbc
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y unixodbc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y uuid-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y va-driver-all
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y vtk6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y x11proto-scrnsaver-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-dev
$SUDO apt-get clean
$SUDO rm -rf /var/lib/apt/lists/*

# pip3 modules should be installed first, then some commands
# (/usr/local/bin/jupyter* for instance) will be replaced by python2
# equivalents when installed by pip2. jupyter modules especially handle
# these conflicts very badly.
$SUDO pip3 install -U numpy
$SUDO pip3 install -U scipy
$SUDO pip3 install nipype
$SUDO pip3 install jupyter
$SUDO pip3 install nbsphinx
$SUDO pip3 install cython
$SUDO pip3 install dipy
$SUDO pip3 install -U nibabel
$SUDO pip3 install sklearn
$SUDO pip3 install -U 'ipython>=5.0,<6.0'
$SUDO pip3 install -U pandas
$SUDO pip3 install -U lark-parser

# WARNING: easy_install gets installed in /usr/local/bin/easy_install
# for python 3! Same for pip, we have to force installing pip for python2
# using the system easy_install (python2)
$SUDO /usr/bin/easy_install pip

# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
$SUDO pip install -U pkgconfig
$SUDO pip install -U cython
$SUDO pip install -U numpy
$SUDO pip install -U setuptools
CPPFLAGS='-I/usr/include/mpi' $SUDO pip install --no-binary=h5py h5py

# ipython / jupyter
$SUDO pip install -U 'ipython>=5.0,<6.0'
$SUDO pip install jupyter
$SUDO pip install -U zmq
$SUDO pip install -U scipy
$SUDO pip install -U nbsphinx
# sphinx 1.7 has bugs
$SUDO pip install -U "sphinx>=1.5,<1.7"

$SUDO pip install nipype
$SUDO pip install dipy
$SUDO pip install -U nibabel
$SUDO pip install sklearn
$SUDO pip install -U pyparsing
$SUDO pip install -U pydot
$SUDO pip install -U pandas
$SUDO pip install -U lark-parser
