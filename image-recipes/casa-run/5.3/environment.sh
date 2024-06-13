# use utf-8 by default
export LANG=C.UTF-8
# avoid having french locale numbers use comas instead of points, which
# disturbs all software and IO
export LC_NUMERIC=C
# add paths for casa-distro container-side tools
export PATH="/casa/host/install/cbin:/casa/host/casa-distro/cbin:/casa/casa-distro/cbin:$PATH"
