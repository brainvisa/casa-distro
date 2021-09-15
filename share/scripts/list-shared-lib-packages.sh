#!/bin/bash

# This script creates a list of packages that contain shared libraries that are
# direct dependencies of any compiled code (executable or shared library)
# contained under a directory passed as argument (typically /casa/host/build
# and /usr/local).

if [ $# -lt 1 ]; then
    echo 'Usage: list-shared-lib-packages.sh [DIRECTORY]...' >&2
    echo '' >&2
    echo 'Typically list-shared-lib-packages.sh /casa/host/build /usr/local' >&2
    echo '(see install_apt_dependencies.sh in casa-distro/image-recipes/casa-run' >&2
    echo 'for more detailed instructions).' >&2
    exit 2
fi

LIST_SHARED_LIBS_PATHS_SH=$(dirname -- "$0")/list-shared-libs-paths.sh
if ! [ -x "$LIST_SHARED_LIBS_PATHS_SH" ]; then
    echo "Error: cannot find companion script list-shared-libs-paths.sh" >&2
    echo "in directory $(dirname -- "$0")" >&2
    exit 1
fi
export LIST_SHARED_LIBS_PATHS_SH

echo 'Looking for shared library dependencies under these directories:' >&2
echo "  $*" >&2
echo 'This will take a few minutes...' >&2

find "$@" \
     \( -name build_files -o -name CMakeFiles \) -prune \
     -o \
     -type f \
     -exec sh -c - "file -b \"\$1\"|grep ^ELF >/dev/null 2>&1 && \"\$LIST_SHARED_LIBS_PATHS_SH\" \"\$1\"" \
     - {} \; \
    | sort -u \
    | while read path; do
        dpkg -S "$(realpath -- "$path")" 2>/dev/null
      done \
    | sed -e 's/\([^:]*\):.*$/\1/' \
    | sort -u
