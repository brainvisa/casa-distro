set -x
apt-get update
apt-get upgrade -y

# Dependencies for Aims
apt-get install -y --no-install-recommends --no-install-suggests \
        libblitz0v5 libsigc++-2.0-0v5 libxml2 libqtcore4 zlib1g python2.7 \
        python-sip libpython2.7 python-pip python-six
        
pip install --disable-pip-version-check --no-cache-dir numpy==1.15.3

# Dependencies for Anatomist
apt-get install -y libqt4-opengl libglu1 python-qt4-gl python-matplotlib

# Dependencies for several Axon toolboxes
apt-get install -y python-scipy libsvm3

# Dependencies for Capsul
apt-get install -y python-traits

# Dependencies for CATI platform
apt-get install -y python-requests python-yaml python-crypto python-xlrd python-dicom

# Useful dependencies
apt-get install -y ipython

mkdir /casa
cp -a /casa_host/install /casa/install

/casa/install/bin/bv_env | cat > /etc/profile.d/brainvisa.sh
chmod a+r /etc/profile.d/brainvisa.sh

