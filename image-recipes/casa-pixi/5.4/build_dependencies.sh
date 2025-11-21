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
    make
    cmake
    pkg-config
#     patch

    # Build dependencies of MESA's libGL
    byacc
    flex
    bison
    libxcb-randr0-dev
    libxrandr-dev
    llvm-dev
    meson
    python3-mako
    xz-utils
    libdrm-dev
    libudev-dev
    libelf-dev
    libz-dev
    libzstd-dev
    libexpat1-dev
    libbsd-dev
    valgrind
    libunwind-dev
    libx11-dev

)
