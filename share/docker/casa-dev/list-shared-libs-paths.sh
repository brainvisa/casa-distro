#!/bin/bash

# Usage:
# $ find /casa/build -type f -execdir sh -c - 'if file -b "$1"|grep ^ELF >/dev/null 2>&1; then ~/list-shared-libs-paths.sh "$1"; fi' - {} \; | tee ~/all-shared-libs-paths.txt
# $ sort -u < ~/all-shared-libs-paths.txt | while read path; do dpkg -S "$path" 2>/dev/null; done | sed -e 's/\([^:]*\):.*$/\1/' | sort -u
#
# This script creates a list of the full paths to all shared libraries that are
# direct dependencies of the executable passed as the first parameter.



# Test if the token $1 is present in the space-separated list $2
in_list() {
    for token in $2; do
        if [ "$1" = "$token" ]; then
            return 0  # TRUE
        fi
    done
    return 1  # FALSE
}


direct_deps=$(objdump -p "$1" \
                  | sed -ne '/^\s*NEEDED.*/ { s/^\s*NEEDED\s*\(.*\)$/\1/; p }')

ldd "$1" | while read line; do
    lib_basename=$(printf '%s' "$line" \
                       | sed -e 's/^\s*\(\S*\)\s*=>.*$/\1/')
    lib_path=$(printf '%s' "$line" \
                   | sed -e 's/^.*=>\s*\(\S*\)\s*(0x[0-9a-fA-F]*)\s*$/\1/')
    if in_list "$lib_basename" "$direct_deps"; then
        echo "$lib_path"
    fi
done
