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
    meson

    # cmake is a build dependency but it should not be removed after
    # compilations,  because it is needed for running ctest tests.
    #
    # cmake

    # Build dependencies of MESA's libGL
    byacc
    flex
    libxcb-randr0-dev
    libxrandr-dev
    llvm-dev
    meson
    python3-mako

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

    # Build dependencies of libminc
    libhdf5-dev
    libnetcdf-dev

    # Build dependencies for draco
    libeigen3-dev

    bison
    libcairo-dev
    libgdk-pixbuf-2.0-dev

    python3-skbuild
    libdraco-dev
)
