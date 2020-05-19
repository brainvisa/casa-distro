#!/bin/bash

# This is a helper script used by list-shared-lib-packages.sh.
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

echo -n "Listing dependencies of $1..." >&2

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

echo ' done' >&2
