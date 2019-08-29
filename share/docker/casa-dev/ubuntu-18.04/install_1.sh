# Install system dependencies for image cati/casa-dev:ubuntu-18.04

set -e # stop the script on error

set -x # display command before running them
if [ `id -u` -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

. /casa/environment.sh



# Install system dependencies

# install python and pip to get apt-mirror-updater
# in order to select an efficient debian mirror.
# (try installing up to 5 times if the default server sometimes disconnects)
for trial in 1 2 3 4 5; do 
    $SUDO apt-get update && break
done
for trial in 1 2 3 4 5; do 
    DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pip && break
done
$SUDO apt-get clean
$SUDO rm -rf /var/lib/apt/lists/*
$SUDO pip install apt-mirror-updater
# setup best mirror in /etc/apt/sources.list
$SUDO apt-mirror-updater -a

DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gnupg2

# add neurodebian repositories and install a few packages
$SUDO wget -O- http://neuro.debian.net/lists/bionic.de-m.full | $SUDO tee /etc/apt/sources.list.d/neurodebian.sources.list
DEBIAN_FRONTEND=noninteractive $SUDO apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9

# WARNING: it is necessary to call apt-get install for each package to
# avoid the 101th package issue
$SUDO apt-get update
$SUDO apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y build-essential
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y cmake
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y cmake-curses-gui
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y subversion
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y git
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sip-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsigc++-2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y zlib1g-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y sqlite3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsqlite3-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnetcdf-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libreadline-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtiff-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjpeg-dev

DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpng-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmng-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y graphviz
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y graphviz-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libminc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdcmtk2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y doxygen
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyro
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-paramiko
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxml2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gfortran
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsvm-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-epydoc
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sphinx
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-matplotlib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openjdk-8-jdk
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libltdl7-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libncurses5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y vim
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y nano
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y wget
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgtk2.0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgtk2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjpeg-turbo8-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-common
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdk-pixbuf2.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y automake
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y texlive-fonts-recommended
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-dicom
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-traits
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y lftp
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y apt-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libblas-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liblapack-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libffi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmpich-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgstreamer1.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgstreamer-plugins-base1.0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liborc-0.4-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxslt1-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libicu-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gdb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mesa-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y x11proto-gl-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-setuptools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y kdesdk-scripts
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y net-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liblapack-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libbz2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libzmq3-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgsl-dev
#DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjasper-dev
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
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-sqlalchemy
#DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-jenkins
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
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sphinx
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sphinx-paramlinks
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pandas
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-xmltodict
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-xmltodict
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-fastcluster
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-sqlalchemy
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-mysqldb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyqt5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y pyqt5-dev-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5opengl5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5svg5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5webkit5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5websockets5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5x11extras5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5xmlpatterns5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5waylandclient5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5webenginewidgets5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5webview5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qtwebengine5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libphonon4qt5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qttools5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqwt-qt5-6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qttools5-dev-tools
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qtmultimedia5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-pyqt5.qtx11extras
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-ipython-genutils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-yaml
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-requests
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-jenkins
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnifti-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y x11proto-print-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y bash-completion
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y unzip
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenjp2-7-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y clang
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qt5-default
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y ghostscript
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqwt-qt5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qtpositioning5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5sensors5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqt5webchannel5-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdouble-conversion-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgraphite2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libharfbuzz-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhyphen-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libwebp-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libwoff-dev
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
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxcb-xinerama0-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-dbg
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y wkhtmltopdf
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-opengl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-joblib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-tqdm
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-joblib
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-tqdm
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python3-dicom
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y default-libmysqlclient-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gdal-data
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y i965-va-driver
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y ibverbs-providers
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libaacs0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libarmadillo-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libarmadillo8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libarpack2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libarpack2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavcodec-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavcodec57
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavformat-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavformat57
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavutil-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libavutil55
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libbdplus0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libbluray2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-atomic-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-chrono-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-container-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-context-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-coroutine-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-date-time-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-exception-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-fiber-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-filesystem-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-graph-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-graph-parallel-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-iostreams-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-locale-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-log-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-math-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-mpi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-mpi-python-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-numpy-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-program-options-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-python-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-random-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-regex-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-serialization-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-signals-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-stacktrace-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-system-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-test-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-thread-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-timer-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-tools-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-type-erasure-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-wave-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libboost-all-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libchromaprint1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libcrystalhd3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdap-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdap25
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdapclient6v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libdapserver7v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libeigen3-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libepsilon-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libepsilon1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libfabric1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libflann-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libflann1.9
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libfreexl-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libfreexl1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libfyba-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libfyba0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdal-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgdal20
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgeos-3.6.2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgeos-c1v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgeos-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgeotiff-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgeotiff2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgif-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgl2ps-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgl2ps1.4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgme0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libgsm1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhdf4-0-alt
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhdf4-alt-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhdf5-mpi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhdf5-openmpi-100
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhdf5-openmpi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libhwloc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libibverbs-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libibverbs1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjson-c-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libjsoncpp-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkml-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmlbase1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmlconvenience1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmldom1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmlengine1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmlregionator1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libkmlxsd1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libminizip-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libminizip1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmp3lame0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmpg123-0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libmysqlclient-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnetcdf-c++4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnetcdf-cxx-legacy-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnl-route-3-200
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libnuma-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libodbc1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libogdi3.2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libogdi3.2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libogg-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenmpi-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenmpi2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenmpt0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenni-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenni-sensor-pointclouds0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenni0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenni2-0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libopenni2-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-apps1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-common1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-features1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-filters1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-io1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-kdtree1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-keypoints1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-ml1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-octree1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-outofcore1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-people1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-recognition1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-registration1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-sample-consensus1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-search1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-segmentation1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-stereo1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-surface1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-tracking1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-visualization1.8
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpoppler-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpoppler-private-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpq-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpq5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libproj-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libproj12
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpsm-infinipath1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqhull-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqhull-r7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libqhull7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y librdmacm1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libshine3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsoxr0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libspatialite-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libspatialite7
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libspeex1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libssh-gcrypt-4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsuperlu-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libsuperlu5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libswresample-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libswresample2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libswscale-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libswscale4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtheora-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtinyxml2.6.2v5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libtwolame0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liburiparser-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y liburiparser1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libutempter0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libva-drm2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libva-x11-2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libva2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvdpau1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvorbisfile3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvpx5
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6-java
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6-jni
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6-qt-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6.3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libvtk6.3-qt
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libwavpack1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libx264-152
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libx265-146
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxerces-c-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxerces-c3.2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxss-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libxvidcore4
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libzvbi-common
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libzvbi0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mesa-va-drivers
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mesa-vdpau-drivers
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mpi-default-bin
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y mpi-default-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y odbcinst
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y odbcinst1debian2
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openmpi-bin
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openmpi-common
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y openni-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y proj-bin
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y proj-data
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-autobahn
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-automat
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-cbor
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-click
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-colorama
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-concurrent.futures
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-constantly
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-hyperlink
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-incremental
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-mpi4py
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-nacl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pam
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-pyasn1-modules
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-qrcode
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-serial
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-service-identity
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-snappy
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-trie
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-trollius
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-twisted
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-twisted-bin
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-twisted-core
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-txaio
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-u-msgpack
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-ubjson
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-vtk6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-wsaccel
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y python-zope.interface
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y qttools5-private-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tcl
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tcl-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tcl-vtk6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tcl8.6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tcl8.6-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tk
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tk-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tk8.6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y tk8.6-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y unixodbc-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y uuid-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y va-driver-all
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y vdpau-driver-all
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y vtk6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y x11proto-scrnsaver-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y xbitmaps
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y xterm 
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y libpcl-dev
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gedit
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y kwrite
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y kate
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y meld
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y kompare
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y kdiff3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gitg
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gitk
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y spyder
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y curl
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | $SUDO bash
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y git-lfs
$SUDO apt-get clean
$SUDO rm -rf /var/lib/apt/lists/*


cd /tmp
wget --no-check-certificate https://github.com/blitzpp/blitz/archive/1.0.1.zip
unzip 1.0.1.zip
cd blitz-1.0.1
./configure
make -j4
$SUDO make -j4 install
cd ..
rm -rf 1.0.1.zip blitz-1.0.1

# remove a few packages that will be reinstalled via pip as newer versions
$SUDO apt-get remove -y python3-scipy
$SUDO apt-get remove -y python-scipy
$SUDO apt-get remove -y python-zmq

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
$SUDO pip3 install -U xlrd
$SUDO pip3 install -U xlwt

# WARNING: easy_install gets installed in /usr/local/bin/easy_install
# for python 3! Same for pip, we have to force installing pip for python2
# using the system easy_install (python2)
$SUDO pip3 install -U 'setuptools==40.8.0'
$SUDO pip3 install -U 'pip<19.1'
PIP3=/usr/local/bin/pip3
$SUDO $PIP3 install -U 'pkgconfig<1.6'
$SUDO $PIP3 install -U 'cython<0.30'
$SUDO $PIP3 install -U 'numpy<1.17'
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
CPPFLAGS='-I/usr/include/mpi' $SUDO $PIP3 install --no-binary=h5py 'h5py<2.10'

$SUDO $PIP3 install -U 'scipy<1.3'
$SUDO $PIP3 install 'nipype<1.2'
$SUDO $PIP3 install -U 'pyzmq<18.1'
$SUDO $PIP3 install -U 'ipython<8'
$SUDO $PIP3 install jupyter
$SUDO $PIP3 install 'qtconsole<4.5'
$SUDO $PIP3 install -U 'nbsphinx<0.5'
$SUDO $PIP3 install 'sphinx-gallery<0.4'
$SUDO $PIP3 install 'dipy<0.15'
$SUDO $PIP3 install -U 'nibabel<2.5'
$SUDO $PIP3 install 'scikit-learn<0.21'
$SUDO $PIP3 install -U 'lark-parser>=0.7,<0.8'
$SUDO $PIP3 install -U 'xlrd<1.3'
$SUDO $PIP3 install -U 'xlwt<1.4'
$SUDO $PIP3 install 'torch'
$SUDO $PIP3 install 'torch-vision'

# pip3 upgrade has overwritten pip, we must reinstall it, not using pip exe
$SUDO python -m pip install -U 'setuptools==40.8.0'
$SUDO python -m pip install -U 'pip<19.1'
PIP2=/usr/local/bin/pip2
$SUDO $PIP2 install -U 'pkgconfig<1.6'
$SUDO $PIP2 install --ignore-installed -U 'cython<0.30'
$SUDO $PIP2 install -U 'numpy<1.17'
# install h5py from sources to force using the system libhdf5,
# otherwise it will install an incompatible binary
CPPFLAGS='-I/usr/include/mpi' $SUDO pip2 install --no-binary=h5py 'h5py<2.10'

# ipython / jupyter
$SUDO $PIP2 install -U 'pyzmq<18.1'
$SUDO $PIP2 install -U 'ipython<6.0'
$SUDO $PIP2 install jupyter
$SUDO $PIP2 install 'qtconsole<4.5'
$SUDO $PIP2 install -U 'scipy<1.3'
$SUDO $PIP2 install -U 'nbsphinx<0.5'
# sphinx 1.7 has bugs
$SUDO $PIP2 install -U "sphinx<1.7"
$SUDO $PIP2 install 'sphinx-gallery<0.4'

$SUDO $PIP2 install 'nipype<1.2'
$SUDO $PIP2 install 'dipy<0.15'
$SUDO $PIP2 install -U 'nibabel<2.5'
$SUDO $PIP2 install 'scikit-learn<0.21'
$SUDO $PIP2 install -U 'pyparsing<2.4'
$SUDO $PIP2 install -U 'pydot<1.3'
$SUDO $PIP2 install "python_jenkins==0.4.16"
$SUDO $PIP2 install -U 'lark-parser>=0.7,<0.8'
$SUDO $PIP2 install -U 'xlrd<1.3'
$SUDO $PIP2 install -U 'xlwt<1.4'
$SUDO $PIP2 install 'torch'
$SUDO $PIP2 install 'torch-vision'

# this one needs reinstalling in pip since the whole module backports has
# changed location... pip is a mess, I tell you...
$SUDO $PIP3 install -U backports.functools_lru_cache
$SUDO $PIP2 install -U backports.functools_lru_cache
