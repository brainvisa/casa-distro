#!/bin/sh

# This script is to be called by Git through the askpass mechanism, see the
# manpage of gitcredentials(7). It will read the BioProj username and password
# from the svn.secret shell script, which is configurable by the user of
# casa-distro.

. /casa/host/conf/svn.secret || exit 1

if [ -z "$SVN_USERNAME" ]; then
    echo 'No SVN_USERNAME variable was found in svn.secret' >&2
    exit 1
fi

if [ "$1" = "Username for 'https://bioproj.extra.cea.fr': " -o "$1" = "Username for 'https://bioproj.cea.fr': " ]; then
    # This informational message must be printed on stderr, because stdout is
    # used for outputting the username.
    echo "Using BioProj credentials stored in svn.secret (username '$SVN_USERNAME')" >&2
    printf '%s' "$SVN_USERNAME" && exit 0
elif [ "$1" = "Password for 'https://${SVN_USERNAME}@bioproj.extra.cea.fr': " -o "$1" = "Password for 'https://${SVN_USERNAME}@bioproj.cea.fr': " ]; then
    if [ -z "$SVN_PASSWORD" ]; then
        echo 'No SVN_PASSWORD variable was found in svn.secret' >&2
        exit 1
    fi
    printf '%s' "$SVN_PASSWORD" && exit 0
fi

# Unrecognized query or printf error. When this askpass script returns an
# error, Git prints an error message and falls back to prompting on the
# terminal.
exit 1
