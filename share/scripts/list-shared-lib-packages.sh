#!/bin/bash

# This script creates a list of packages that contain shared libraries that are
# direct dependencies of any compiled code (executable or shared library)
# contained under a directory passed as argument (typically /casa/build and
# /usr/local).

if [ $# -lt 1 ]; then
    echo 'Usage: list-shared-lib-packages.sh [DIRECTORY]...' >&2
    echo '' >&2
    echo 'Typically list-shared-lib-packages.sh /casa/build /usr/local' >&2
    echo '(see install_apt_dependencies.sh in casa-distro/image-recipes/casa-run' >&2
    echo 'for more detailed instructions).' >&2
    exit 2
fi

echo 'Looking for shared library dependencies under these directories:' >&2
echo "  $*" >&2
echo 'This will take a few minutes...' >&2

find "$@" \
     \( -name build_files -o -name CMakeFiles \) -prune \
     -o \
     -type f \
     -execdir sh -c - 'file -b "$1"|grep ^ELF >/dev/null 2>&1 && /casa/list-shared-libs-paths.sh "$1"' \
     - {} \; \
    | sort -u \
    | while read path; do
        dpkg -S "$path" 2>/dev/null
      done \
    | sed -e 's/\([^:]*\):.*$/\1/' \
    | sort -u
