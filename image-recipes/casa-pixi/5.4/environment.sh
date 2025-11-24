# use utf-8 by default
export LANG=C.UTF-8
# avoid having french locale numbers use comas instead of points, which
# disturbs all software and IO
export LC_NUMERIC=C

if [ -z "$XDG_CACHE_HOME" ]; then
    # try to share cache dir with host home
    if [ $(stat -t -c "%D" "$HOME") = $(stat -t -c "%D" "$CASA_HOST_HOME/.cache") ]; then
        export XDG_CACHE_HOME=$CASA_HOST_HOME/.cache
    fi
fi

# hook for installing in pixi at first run
if [ -f "/casa/host/install/.bv_update_links" ]; then
    _cwd="$(pwd)"
    cd /casa/host/install
    pixi run bv_update_bin_links
    rm "/casa/host/install/.bv_update_links"
    cd "$_cwd"
    unset _cwd
    _run_bv=1
fi

# add paths for casa-distro container-side tools
export PATH="/casa/host/install/cbin:/casa/host/casa-distro/cbin:/casa/casa-distro/cbin:$PATH"

if [ -n "$_run_bv" ]; then
    exec /casa/host/install/bin/bv "$@"
fi
