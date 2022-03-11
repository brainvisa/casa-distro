# This bash script is sourced by both install_apt_dependencies.sh and
# cleanup_build_dependencies.sh.
#
# Every package that is on this list will be installed by
# install_apt_dependencies.sh, then removed in cleanup_build_dependencies.sh

build_dependencies=(
    # General build dependencies (notably useful for pip-compiled packages)
    g++
    gcc
    git
    libc-dev
    libpython3-dev
    make
    patch
    pkg-config

    # cmake is a build dependency but it should not be removed after
    # compilations,  because it is needed for running ctest tests.
    #
    # cmake

    # Build dependencies of MIRCen's fork of openslide
    autoconf
    automake
    libtool
    pkg-config  # needed for autoreconf
    libopenjp2-7-dev
    libtiff-dev
    libcairo2-dev
    libgdk-pixbuf2.0-dev
    libglib2.0-dev
    libxml2-dev
    libjxr-dev

    # Build dependencies of libXp
    x11proto-print-dev

    # Build dependencies of python-pcl
    libpcl-dev  # for python-pcl

    # Build dependencies of SIP/PyQt
    libqt5svg5-dev  # qtconsole needs PyQt5.QtSvg
    qtwebengine5-dev  # for PyQt
)
