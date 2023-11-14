# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import datetime
import glob
import json
import os
import os.path as osp
from pprint import pprint
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile

from casa_distro.command import command, check_boolean
from casa_distro.defaults import (default_base_directory,
                                  publish_url, default_download_url)
from casa_distro.environment import (BBIDaily,
                                     casa_distro_directory,
                                     iter_environments,
                                     run_container,
                                     select_environment,
                                     get_run_base_of_dev_image)
from casa_distro.log import verbose_file, boolean_value
import casa_distro.singularity
import casa_distro.vbox
import casa_distro.docker
from casa_distro.hash import file_hash
from .image_builder import get_image_builder, LocalInstaller


_true_str = re.compile('^(?:yes|true|y|1)$', re.I)
_false_str = re.compile('^(?:no|false|n|0|none)$', re.I)


def str_to_bool(string):
    if _false_str.match(string):
        return False
    if _true_str.match(string):
        return True
    raise ValueError('Invalid value for boolean: ' + repr(string))


@command
def singularity_deb(dockerhub='ubuntu:20.04',
                    output_dir=osp.abspath(os.curdir),
                    version='3.8.3',
                    go_version='1.17'):
    """Create a Debian package to install Singularity.
    Perform the whole installation process from a rw system and Singularity
    source. Then put the result in a ``*.deb`` file.

    Parameters
    ----------
    dockerhub:
        default={dockerhub_default}

        Name of the base image system to pull from DockerHub.
    output_dir:
        default={output_dir_default}

        Location of the resulting Debian package file.
    version:
        default={version_default}

        Version of Singularity to use. This must be a valid release version.
        Go language is not included in the final package.
    """

    tmp = tempfile.mkdtemp(prefix='singularity-container-deb-')
    singularity_image = 'singularity_image'
    try:
        build_sh = osp.join(tmp, 'build.sh')
        open(build_sh, 'w').write('''#!/bin/sh
set -xe
umask 0022  # avoid Lintian warning non-standard-file-perm
OS=linux
ARCH=amd64
DEB_HOST_MULTIARCH=x86_64-linux-gnu
ID=
VERSION_ID=
. /etc/os-release  # sets the ID and VERSION_ID variables
DISTRIB=${ID}-${VERSION_ID}
package_version=${SINGULARITY_VERSION}~${DISTRIB}
#Installation des packages requis
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential uuid-dev \
    libgpgme-dev squashfs-tools libseccomp-dev wget pkg-config git \
    cryptsetup-bin libssl-dev
# Download and install GO
rm -rf /usr/local/go
wget -O $TMP/go${GO_VERSION}.${OS}-${ARCH}.tar.gz \
    https://dl.google.com/go/go${GO_VERSION}.${OS}-${ARCH}.tar.gz
tar -C /usr/local -xzf $TMP/go${GO_VERSION}.${OS}-${ARCH}.tar.gz
rm -f $TMP/go${GO_VERSION}.${OS}-${ARCH}.tar.gz
export GOPATH=${HOME}/go
export GOROOT=/usr/local/go
export PATH=$GOROOT/bin:$PATH:${GOPATH}/bin
# Download the requested Singularity release
wget -O $TMP/singularity-ce-${SINGULARITY_VERSION}.tar.gz \
    https://github.com/sylabs/singularity/releases/download/v${SINGULARITY_VERSION}/singularity-ce-${SINGULARITY_VERSION}.tar.gz
mkdir -p ${GOPATH}/src/github.com/sylabs
tar -C ${GOPATH}/src/github.com/sylabs -zxf \
    $TMP/singularity-ce-${SINGULARITY_VERSION}.tar.gz
# Build and install Singularity into DESTDIR
export DESTDIR=$TMP/singularity-ce_${package_version}_amd64
rm -rf ${DESTDIR}
cd ${GOPATH}/src/github.com/sylabs/singularity-ce-${SINGULARITY_VERSION}
./mconfig \
    -P release-stripped \
    --prefix=/usr \
    --sysconfdir=/etc \
    --libexecdir=/usr/lib/${DEB_HOST_MULTIARCH} \
    --localstatedir=/var/lib
make -C ./builddir
make -C ./builddir install DESTDIR=${DESTDIR}
mkdir -p ${DESTDIR}/DEBIAN
cat <<EOF > ${DESTDIR}/DEBIAN/control
Package: singularity-ce
Version: ${package_version}
Maintainer: BrainVISA release team <admin@brainvisa.info>
Architecture: ${ARCH}
Section: admin
Priority: optional
Depends: squashfs-tools, ca-certificates, cryptsetup-bin, libc6, libseccomp2
Conflicts: singularity-container
Replaces: singularity-container (<< ${SINGULARITY_VERSION})
Recommends: e2fsprogs
Homepage: https://www.sylabs.io/
Description: container platform focused on supporting "Mobility of Compute"
 Mobility of Compute encapsulates the development to compute model
 where developers can work in an environment of their choosing and
 creation and when the developer needs additional compute resources,
 this environment can easily be copied and executed on other platforms.
 Additionally as the primary use case for Singularity is targeted
 towards computational portability, many of the barriers to entry of
 other container solutions do not apply to Singularity making it an
 ideal solution for users (both computational and non-computational)
 and HPC centers.
EOF
# Fix Lintian warning setuid-binary
mkdir -p ${DESTDIR}/usr/share/lintian/overrides
cat <<EOF > ${DESTDIR}/usr/share/lintian/overrides/singularity-ce
# Singularity requires root suid for operation:
setuid-binary usr/lib/*/singularity/bin/*-suid 4755 root/root
EOF
# Fix Lintian warning package-installs-into-obsolete-dir
mkdir -p ${DESTDIR}/usr/share/bash-completion/completions
mv ${DESTDIR}/etc/bash_completion.d/* \
    ${DESTDIR}/usr/share/bash-completion/completions/
rmdir ${DESTDIR}/etc/bash_completion.d/
# Fix Lintian warning file-in-etc-not-marked-as-conffile
find ${DESTDIR}/etc ! -type d -print \
    | sed -e "s!^${DESTDIR%/}!!" \
    > ${DESTDIR}/DEBIAN/conffiles
dpkg-deb --build ${DESTDIR} "$TMP"
''')

        subprocess.check_call(['singularity', 'build',
                               '--fakeroot',
                               '--disable-cache',
                               '--sandbox', singularity_image,
                               'docker://{}'.format(dockerhub)],
                              cwd=tmp)
        subprocess.check_call(['singularity', 'run',
                               '--writable',
                               '--fakeroot',
                               '--home', tmp,
                               '--env', 'TMP={}'.format(tmp),
                               '--env', 'GO_VERSION={}'.format(go_version),
                               '--env',
                               'SINGULARITY_VERSION={}'.format(version),
                               singularity_image,
                               'sh', build_sh],
                              cwd=tmp)
        deb = osp.basename(glob.glob(osp.join(tmp, '*.deb'))[0])
        shutil.move(osp.join(tmp, deb), osp.join(output_dir, deb))
    finally:
        # cleanup with singularity to take into account files
        # created with --fakeroot not belonging to current user
        subprocess.check_call(['singularity', 'exec', '--disable-cache',
                               '--fakeroot', 'library://alpine', 'rm',
                               '-Rf', tmp])


@command
def create_base_image(type,
                      image_version,
                      name='casa-{type}-{image_version}',
                      base=None,
                      output=osp.join(default_base_directory,
                                      '{name}.{extension}'),
                      container_type='singularity',
                      verbose=True,
                      **kwargs):
    """Create a new virtual image

    Creating the casa-system image:

    - For Singularity you need to run these commands in order to create the
      casa-system image::

          cd "$CASA_BASE_DIRECTORY"
          singularity pull ubuntu-18.04.sif docker://ubuntu:18.04

      Then you can directly use the ubuntu image as base for the run image. You
      may build a "system" image as follows, but it's not needed::

          casa_distro_admin create_base_image base=ubuntu-18.04.sif \\
              type=system image_version=5.0

    - For VirtualBox:

      1. Download a Ubuntu image to your CASA base directory, e.g.
         lubuntu-22.04.1-desktop-amd64.iso

      2. Run create_user_image::

          casa_distro_admin create_user_image \\
              container_type=vbox \\
              type=system \\
              base=lubuntu-22.04.1-desktop-amd64.iso \\
              image_version=5.3

      3. Follow the instructions that are printed in the terminal to install
         and configure Lubuntu appropriately.

    Parameters
    ----------
    type
        type of image to publish. Either "system" for a base system image, or
        "run" for an image used in a user environment, or "dev" for a developer
        image.

    {name}

    base
        Source file used to build the image. The default value depends on image
        type and container type.

    output
        default={output_default}

        File location where the image is created.

    container_type
        default={container_type_default}

        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker".

    image_version
        default={image_version_default}

        Version (or branch) of the image

    {verbose}

    cleanup (effective only if container_type=singularity)
        default=yes

        If "no", "false" or "0", do not cleanup after a failure during image
        building. This may allow to debug a problem after the failure. For
        instance, with Singularity one can use a command like::

            sudo singularity run --writable
            /tmp/rootfs-79744fb2-f3a7-11ea-a080-ce9ed5978945 /bin/bash

    force (allowed only if container_type=singularity)
        default=no

        If ``yes``, ``true`` or 1, erase existing image without asking any
        question.

    fakeroot (allowed only if container_type=singularity)
        default=yes

        If ``yes``, ``true`` or 1, use singularity --fakeroot for building the
        images (this is the recommended wby). Otherwise, "sudo singularity"
        must be used so singularity has root access on the host.

    memory (allowed only if container_type=vbox)
        default=8192

        Size in MiB of memory allocated for virtual machine.

    video_memory (allowed only if container_type=vbox)
        default=50

        Size in MiB of video memory allocated for virtual machine.

    disk_size (allowed only if container_type=vbox)
        default=131072

        For vbox container type only. Size in MiB of maximum disk size of
        virtual machine.

    gui (allowed only if container_type=vbox)
        default=no

        For vbox container type only. If value is "yes", "true" or "1", display
        VirtualBox window.
    """  # noqa: E501
    verbose = verbose_file(verbose)

    if type not in ('system', 'run', 'dev'):
        raise ValueError('Image type can only be "system", "run" or "dev"')

    if container_type == 'singularity':
        origin_extension = 'sif'
        extension = 'sif'
    elif container_type == 'vbox':
        origin_extension = 'iso'
        extension = 'ova'
    # elif container_type == 'docker':
    #     origin_extension = ''
    #     extension = ''
    else:
        raise ValueError('Unsupported container type: %s' % container_type)

    if type == 'system':
        image_builder = None
    else:
        image_recipes_dir = osp.join(
            osp.dirname(osp.dirname(osp.dirname(__file__))),
            'image-recipes')
        build_file = osp.join(image_recipes_dir,
                              'casa-%s' % type,
                              image_version,
                              'build_image.py')
        image_builder = get_image_builder(build_file)

    if base is None:
        if type == 'system':
            base = osp.join(
                default_base_directory,
                '*ubuntu-*.{extension}'.format(extension=origin_extension))
        else:
            base = osp.join(default_base_directory,
                            image_builder.base.format(extension=extension))

    if not osp.exists(base):
        base_pattern = osp.expandvars(osp.expanduser(base))
        if verbose:
            print('Looking for base in', base_pattern,
                  file=verbose)
        bases = glob.glob(base_pattern)
        if len(bases) == 0:
            # Raise appropriate error for non existing file
            open(base)
        elif len(bases) > 1:
            raise ValueError(
                'Several base images found : {0}'.format(', '.join(bases)))
        base = bases[0]

    base = os.path.join(default_base_directory, base)  # make path absolute

    if osp.exists(base + '.json'):
        base_metadata = json.load(open(base + '.json'))
    else:
        base_metadata = {}
    system = base_metadata.get('system')
    if system is None:
        distro, version = osp.basename(base).split('-')[:2]
        if 'ubuntu' in distro:
            distro = 'ubuntu'
        version = '.'.join(version.split('.')[:2])
        system = '%s-%s' % (distro, version)

    name = name.format(type=type, system=system, image_version=image_version)
    output = osp.expandvars(osp.expanduser(output)).format(name=name,
                                                           system=system,
                                                           extension=extension)

    metadata_output = output + '.json'
    metadata = {
        'name': name,
        'type': type,
        'system': system,
        'container_type': container_type,
        'creation_time': datetime.datetime.now().isoformat(),
        'image_version': image_version,
    }
    origin = base_metadata.get('origin')
    if origin:
        metadata['origin'] = origin
    elif type == 'system':
        metadata['origin'] = os.path.basename(base)
    if type == 'dev':
        metadata['origin_run'] = base_metadata['image_id']
    metadata['compatibility'] = []

    if verbose:
        print('Creating', output, file=verbose)
        print('based on', base, file=verbose)
        if image_builder:
            print('using', image_builder.build_file, file=verbose)
        print('metadata = ', end='', file=verbose)
        pprint(metadata, stream=verbose, indent=4)
    json.dump(metadata, open(metadata_output, 'w'),
              indent=4, separators=(',', ': '))

    if container_type == 'vbox':
        module = casa_distro.vbox
    elif container_type == 'singularity':
        module = casa_distro.singularity
    elif container_type == 'docker':
        module = casa_distro.docker
    else:
        raise ValueError('Unsupported container type: %s' % container_type)

    image_id, msg = module.create_image(base, base_metadata,
                                        output, metadata,
                                        image_builder=image_builder,
                                        verbose=verbose,
                                        **kwargs)
    if msg:
        print(msg)
    elif osp.isfile(output):
        metadata['size'] = os.stat(output).st_size
        metadata['md5'] = file_hash(output)
        metadata['image_id'] = image_id
        json.dump(metadata, open(metadata_output, 'w'),
                  indent=4, separators=(',', ': '))


def create_numbered_file(url, filename, metadata):
    script = '''from __future__ import print_function
import os, sys
import json
import glob
import re
import hashlib

def file_hash(path, blocksize=2**20):
    m = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()

def check_image(metadata, meta_filename):
    'True if meta_filename is up-to-date'

    if not os.path.exists(os.path.splitext(meta_filename)[0]):
        return False
    image_id = metadata['image_id']
    with open(meta_filename) as f:
        imeta = json.load(f)
    if imeta.get('image_id') == image_id:
        md5 = file_hash(os.path.splitext(meta_filename)[0])
        if md5 == imeta['md5']:
            return True
    return False

try:

    filename = "%s"
    metadata = %s
    done = False
    num = None

    filename_base, ext = os.path.splitext(filename)
    if ext == '.json':
        filename_base, ext2 = os.path.splitext(filename_base)
        ext = ''.join([ext2, ext])

    filename_pattern = '%%s-%%%%s%%s' %% (filename_base, ext)
    nums = []

    if os.path.exists(filename):
        if check_image(metadata, filename):
            print(filename)
            print()
            print('-- up-to-date --')
            sys.exit(0)
        nums.append(0)

    e = glob.glob(filename_pattern %% '*')
    if e:
        nums += sorted(
            [int(re.match(filename_pattern %% '([0-9]+)', x).group(1))
                for x in e])

        for en, i in zip(e, nums):
            if check_image(metadata, en):
                print(en)
                print(i)
                print('-- up-to-date --')
                sys.exit(0)

    if nums:
        num = nums[-1] + 1
    else:
        num = 1

    while not done:
        if num is not None:
            new_filename = filename_pattern %% str(num)
        else:
            new_filename = filename
            num = 0
        try:
            fd = os.open(new_filename, os.O_CREAT | os.O_EXCL)
            os.close(fd)
            done = True
            print(new_filename)
            print(num)
            metadata['build_number'] = num
            with open(new_filename, 'w') as f:
                json.dump(metadata, f, indent=4, separators=(',', ': '))
        except OSError:
            if num is None:
                num = 1
            else:
                num += 1

finally:
    os.unlink(sys.argv[0])
''' % (filename, repr(metadata))

    script_filename = tempfile.mkstemp()
    os.close(script_filename[0])

    try:

        with open(script_filename[1], 'w') as f:
            f.write(script)

        cmd = ['ssh', url, 'tempfile']
        remote_script_filename = subprocess.check_output(cmd).strip().decode()

        subprocess.check_call(['rsync',
                               script_filename[1],
                               '%s:%s' % (url, remote_script_filename)])

        cmd = ['ssh', url]
        cmd += ['python', remote_script_filename]

        num_output = [x.strip()
                      for x in
                      subprocess.check_output(cmd).strip().decode().split(
                          '\n')]

        final_filename = num_output[0]
        num = num_output[1]
        if not num or num == 'None':
            num = 0
        up_to_date = False
        if len(num_output) >= 3 and num_output[2] == '-- up-to-date --':
            up_to_date = True
        return (final_filename, int(num), up_to_date)

    finally:
        os.unlink(script_filename[1])


@command
def publish_base_image(type=None,
                       image=osp.join(
                           default_base_directory,
                           'casa-{type}-*.{extension}'),
                       container_type='singularity',
                       verbose=True):
    """Upload an image to BrainVISA web site.

    Upload is done with rsync in the following remote directory:

      {publish_url}

    This directory location can be customized with
    the following environment variables::

        BRAINVISA_PUBLISH_LOGIN (default=brainvisa)
        BRAINVISA_PUBLISH_SERVER (default=brainvisa.info)
        BRAINVISA_PUBLISH_DIR (default=/var/www/html/brainvisa.info_download)

    Parameters
    ----------

    type
        type of image to publish. Either "system" for a base system image, or
        "run" for an image used in a user environment, or "dev" for a developer
        image.

    {image}

    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker".

    {verbose}
    """
    verbose = verbose_file(verbose)
    if container_type == 'singularity':
        extension = 'sif'
    elif container_type == 'vbox':
        extension = 'ova'
    else:
        raise ValueError('Unsupported container type: %s' % container_type)

    image = image.format(type=type,
                         extension=extension)
    if not osp.exists(image):
        images = glob.glob(osp.expandvars(osp.expanduser(image)))
        if len(images) == 0:
            # Raise appropriate error for non existing file
            open(image)
        elif len(images) > 1:
            # remove symlinks because they appear as duplicates
            images = [im for im in images if not osp.islink(im)]
            if len(images) > 1:
                raise ValueError(
                    'Several image files found : {0}'.format(
                        ', '.join(images)))
        image = images[0]

    # Add image file md5 hash to JSON metadata file
    metadata_file = image + '.json'
    metadata = json.load(open(metadata_file))
    metadata['size'] = os.stat(image).st_size
    metadata['md5'] = file_hash(image)

    url, remote_path = publish_url.split(':', 1)
    remote_metadata_file = osp.join(remote_path, osp.basename(metadata_file))

    final_metafile, num, up_to_date = create_numbered_file(
        url, remote_metadata_file, metadata)
    if up_to_date:
        print('Image %s is up-to-date on the server'
              % osp.basename(final_metafile))
        return
    metadata['build_number'] = num

    json.dump(metadata, open(metadata_file, 'w'),
              indent=4, separators=(',', ': '))

    final_imagefile = osp.splitext(final_metafile)[0]
    print('final_imagefile:', repr(final_imagefile))
    image_path, image_base = osp.split(image)
    subprocess.check_call(['rsync', '-P', '--progress', '--chmod=a+r',
                           image, '%s:%s' % (url, final_imagefile)])
    # symlink numbered filename on local filesystem
    if osp.basename(final_imagefile) != image_base:
        os.symlink(image, osp.join(image_path, osp.basename(final_imagefile)))
        os.symlink(metadata_file,
                   osp.join(image_path, osp.basename(final_metafile)))


@command
def create_user_image(
        version,
        name='{distro}-{version}',
        base_image='{base_directory}/casa-run-{image_version}{extension}',
        distro=None,
        branch=None,
        system=None,
        image_version=None,
        environment_name=None,
        container_type=None,
        output='{base_directory}/{name}{extension}',
        force='no',
        base_directory=casa_distro_directory(),
        install='yes',
        install_doc='yes',
        install_test='yes',
        install_thirdparty='none',
        generate='yes',
        zip='no',
        verbose=True,
        cleanup='yes',
        **kwargs):
    """Create a "user" image given a development environment.
    The development environment is selected among existing ones its
    distro and system or simply by its name. Only development environments
    using the master branch are considered.
    This command can perform three steps. Each step can be ignored by setting
    the corresponding option to "no" :

    - install: perform an installation of the development environment into its
      installation directory. This modify the development environment by
      updating its installation directory.

    - generate: generate a new image for the development environment. The new
      image is based on base_image and the installation directory of the
      development environment is copied into the image in /casa/install.


    Parameters
    ----------
    version [REQUIRED]
        Version of the release to create.
    name
        default={name_default}
        Name given to the created image.
    base_image
        default={base_image_default}
        Name of the "run" image used to generate the new user image
    {distro}
    {branch}
    {system}
    {image_version}
    environment_name
        If given, select dev environment by its name.
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker".
    output
        default={output_default}
        Path of the output image.
    force
        default={force_default}
        If "yes", "true" or 1, erase existing image without asking any
        question.
    fakeroot (allowed only if container_type=singularity)
        default=yes
        If ``yes``, ``true`` or 1, use singularity --fakeroot for building the
        images (this is the recommended wby). Otherwise, "sudo singularity"
        must be used so singularity has root access on the host.
    {base_directory}
    install
        default={install_default}
        If "true", "yes" or "1", perform the installation steps:
        'make install-runtime', as well as 'make install-doc' and
        'make install-test', depending on the install_doc and install_test
        parameters.
        If "false", "no" or "0", skip all installation steps
    install_doc
        default={install_doc_default}
        If "true", "yes" or "1", run 'make install-doc' as part of the install
        step.
        If "false", "no" or "0", skip this step
    install_test
        default={install_test_default}
        If "true", "yes" or "1", run 'make install-test' as part of the install
        step.
        If "false", "no" or "0", skip this step
    install_thirdparty
        default={install_thirdparty_default}
        If "none", no third-party software is installed in the image. If
        "all", all available software will be installed during the ``generate``
        step. If "default", a default list of software will be installed. If
        starting with "file://", then the thirdparty install list will be read
        from a JSON file. Other values are understood as a list of software
        ("spm12-standalone,freesurfer"). Each will be installed from their host
        system location into ``/usr/local`` on the container image. Software
        location will be searched in a small search list (/usr/local,
        /drf/local, /i2bm/local). If installed in another location, this
        location may be passed after a ``=`` sign in the software name, ex:
        ``spm12-standalone=/opt/spm,freesurfer``.
        If a JSON file is used, then the file syntax is a dictionary, keys are
        thirdparty software names ("spm12-standalone"), and values are
        directories. If default locations are expected, then the value may be
        null.
    generate
        default={generate_default}
        If "true", "yes" or "1", perform the image creation step.
        If "false", "no" or "0", skip this step
    cleanup
        default={cleanup_default}
        If "false", "no" or "0", do NOT clean up the temp image during the
        generate step after failed build, can be helpful for debugging
    zip
        default={zip_default}
        If "true", "yes" or "1", zip the installed files for an "online"
        installation.
    {verbose}

    """
    base_directory = os.path.abspath(base_directory)
    install = check_boolean('install', install)
    install_doc = check_boolean('install_doc', install_doc)
    install_test = check_boolean('install_test', install_test)
    generate = check_boolean('generate', generate)
    cleanup = check_boolean('cleanup', cleanup)
    zip = check_boolean('zip', zip)

    verbose = verbose_file(verbose)
    config = select_environment(base_directory,
                                type='dev',
                                distro=distro,
                                branch=branch,
                                system=system,
                                image_version=image_version,
                                name=environment_name,
                                container_type='singularity')
    if container_type != 'vbox':
        container_type = config['container_type']
    if container_type == 'singularity':
        extension = '.sif'
        module = casa_distro.singularity
    elif container_type == 'vbox':
        extension = '.ova'
        module = casa_distro.vbox
    else:
        raise ValueError('Unsupported container type: {0}'.format(
            container_type))
    name = name.format(version=version, **config)
    kwargs = config.copy()
    kwargs.pop('name', None)
    output = osp.expandvars(osp.expanduser(output)).format(
        name=name,
        extension=extension,
        base_directory=base_directory,
        **kwargs
    )
    force = boolean_value(force)

    # update distro name
    distro = config['distro']

    metadata = {
        'name': name,
        'type': 'user',
        'distro': config['distro'],
        'system': config['system'],
        'image_version': config['image_version'],
        'version': version,
        'container_type': container_type,
        'creation_time': datetime.datetime.now().isoformat(),
        'origin_dev': config.get('image_id'),
    }
    base_image_pattern = base_image.format(base_directory=base_directory,
                                           extension=extension,
                                           **metadata)
    base_images = glob.glob(base_image_pattern)
    if len(base_images) == 0:
        base_image_pattern_patch \
            = base_image.format(base_directory=base_directory,
                                extension='-*%s' % extension,
                                **metadata)
        base_images = glob.glob(base_image_pattern_patch)
        if len(base_images) == 0:
            raise ValueError(
                'Cannot find file: {} or {}'.format(base_image_pattern,
                                                    base_image_pattern_patch))

    if 'origin_run' not in config:
        dev_json = osp.join(config['directory'], config['image']) + '.json'
        dev_config = {}
        if osp.exists(dev_json):
            with open(dev_json) as f:
                dev_config = json.load(f)
        if 'origin_run' in dev_config:
            config['origin_run'] = dev_config['origin_run']
        else:
            print('warning, dev image does not have run image info. '
                  'Cannot check consistency.', file=sys.stderr)
            if len(base_images) != 1:
                raise ValueError(
                    'Found several images: {}'.format(', '.join(base_images)))

    base_found = False
    for base_image in base_images:
        with open('%s.json' % base_image) as f:
            base_metadata = json.load(f)
            if base_metadata.get('image_id') == config.get('origin_run'):
                base_found = True
                break

    if not base_found:
        if len(base_images) == 1:
            print('mismatching run images in dev metadata and the one found '
                  'here.', file=sys.stderr)
        else:
            raise ValueError('No matching run image found from dev metadata')

    print('using run image:', base_image)
    metadata['origin_run'] = base_metadata.get('image_id')

    # check whether the dev environment image is compatibe with the base run
    # image
    if 'origin_run' not in config:
        print('warning, dev image does not have run image info. '
              'Cannot check consistency.', file=sys.stderr)
        print(config)
    else:
        if (metadata.get('container_type') != 'vbox'
                and metadata['origin_run'] != config.get('origin_run')):
            # not the same: smells rotten but the run image may be compatibe
            # with the (older) used for the dev image
            compat = base_metadata.get('compatibility', [])
            if config.get('origin_run') not in compat:
                raise ValueError(
                    'The base run image is not compatible with the dev image')

    if install:
        # Always empty the directory before installing to avoid files left over
        # from a previous install.
        shutil.rmtree(osp.join(config['directory'], 'install'))
        os.mkdir(osp.join(config['directory'], 'install'))

        install_targets = ['install-runtime']
        install_targets += ['install-doc'] if install_doc else []
        install_targets += ['install-test'] if install_test else []
        # install_doc and install_test also depend on install-runtime and
        # will do it again
        # we use bash -c 'make...' in order to allow user .profile
        # customization (paths for Qt6 in pip install...)
        sub_cmd = [
            'bv_env_test',
            'make',
            'BRAINVISA_INSTALL_PREFIX=/casa/host/install'] \
            + install_targets
        retcode = run_container(
            config=config,
            command=[
                'bash',
                '-c',
                ' '.join(sub_cmd)],
            gui=False,
            opengl="container",
            root=False,
            cwd='/casa/host/build',
            env={},
            image=None,
            container_options=None,
            base_directory=base_directory,
            verbose=verbose
        )
        if retcode != 0:
            sys.exit('make ' + ' '.join(install_targets)
                     + ' failed, aborting.')
        sub_cmd = ['bv_env_test',
                   'make',
                   'BRAINVISA_INSTALL_PREFIX=/casa/host/install',
                   'post-install']
        retcode = run_container(
            config=config,
            command=['bash',
                     '-c',
                     ' '.join(sub_cmd)],
            gui=False,
            opengl="container",
            root=False,
            cwd='/casa/host/build',
            env={},
            image=None,
            container_options=None,
            base_directory=base_directory,
            verbose=verbose
        )
        if retcode != 0:
            sys.exit('make post-install failed, aborting.')

    zip_archive = osp.join(config['directory'],
                           '%(distro)s-%(version)s-%(system)s.zip' % metadata)
    zip_json = '%s.json' % zip_archive

    if zip:
        print('Creating zip file for distro', distro, '...')
        with zipfile.ZipFile(zip_archive, 'w', allowZip64=True,
                             compression=zipfile.ZIP_DEFLATED) as zip:
            for root, dirs, files in os.walk(osp.join(config['directory'],
                                                      'install')):
                rel = osp.relpath(root, osp.join(config['directory'],
                                                 'install'))
                for dir in dirs:
                    zip.write(osp.join(root, dir), osp.join(rel, dir))
                for file in files:
                    zip.write(osp.join(root, file), osp.join(rel, file))
        zip_meta = {
            'md5': file_hash(zip_archive),
            'size': os.stat(zip_archive).st_size,
            'distro': distro,
            'system': config['system'],
            'image_version': config['image_version'],
            'version': version,
            'creation_time': datetime.datetime.now().isoformat(),
        }
        with open(zip_json, 'w') as jf:
            json.dump(zip_meta, jf, indent=4, separators=(',', ': '))
        print('zip file created:', zip_archive)

    metadata_file = output + '.json'

    if generate:
        output_dir = osp.dirname(output)
        if not osp.exists(output_dir) and output_dir != '':
            os.makedirs(output_dir)
        # filter kwargs to avoid passing unexpected or duplicate parameters
        kwargs = {k: v for k, v in kwargs.items()
                  if k in ('fakeroot', )}
        image_id, msg = module.create_user_image(
            base_image=base_image,
            dev_config=config,
            version=version,
            output=output,
            force=force,
            base_directory=base_directory,
            verbose=verbose,
            install_thirdparty=install_thirdparty,
            cleanup=cleanup,
            **kwargs)
        if msg:
            print(msg)

        # Add image file md5 hash to JSON metadata file
        metadata['size'] = os.stat(output).st_size
        metadata['md5'] = file_hash(output)
        metadata['image_id'] = image_id
        json.dump(metadata, open(metadata_file, 'w'),
                  indent=4, separators=(',', ': '))


@command
def publish_user_image(image):
    """Upload a "user" image to the BrainVISA web site.

    Upload is done with rsync in the following remote directory:

      {publish_url}

    This directory location can be customized with
    the following environment variables::

        BRAINVISA_PUBLISH_LOGIN (default=brainvisa)
        BRAINVISA_PUBLISH_SERVER (default=brainvisa.info)
        BRAINVISA_PUBLISH_DIR (default=/var/www/html/brainvisa.info_download)

    Parameters
    ----------

    {image}
    """
    files = [image + '.json', image]
    print('uploading files to server:')
    subprocess.check_call(['rsync', '-P', '--progress', '--chmod=a+r']
                          + files + [publish_url])


NONFATAL_BV_MAKER_STEPS = {'doc', 'test'}
"""bv_maker steps whose failure still allows to proceed to further testing."""


@command
def bbi_daily(distro=None, branch=None, system=None,
              image_version=None, name=None,
              jenkins_server=None,
              jenkins_auth='{base_directory}/jenkins_auth',
              jenkins_password=None,
              update_casa_distro='yes',
              update_base_images='yes',
              bv_maker_steps='sources,configure,build,doc',
              dev_tests='yes',
              update_user_images='yes',
              recreate_user_envs='yes',
              user_tests='yes',
              base_directory=casa_distro_directory(),
              install_thirdparty='none',
              verbose=None):
    '''BrainVISA Build infrastructure: daily/nightly automated tests

    In BrainVISA Build Infrastructure (BBI), the ``casa_distro_admin
    bbi_daily`` command orchestrates automated builds and tests in a given
    *base directory*. The ``bbi_daily`` command will run the following steps,
    while (optionally) logging detailed output to a Jenkins server. See
    :doc:`nightly` for a complete introduction to automated tests.

    1. Self-update casa_distro using 'git pull' and restart itself for the next
       steps
    2. Select *dev* environments based on the provided filters (distro, branch,
       system, image_version, name)
    3. Update casa-dev and casa-run images used by the selected environments to
       the latest version available from the BrainVISA website
    4. For every selected *dev* environment, perform the following tasks:

       1. ``bv_maker sources``
       2. ``bv_maker configure``
       3. ``bv_maker build``
       4. ``bv_maker doc``
       5. perform all tests in the *dev* environment (running the same commands
          as ``bv_maker test``)
       6. create or update a user image with ``casa_distro_admin
          create_user_image`` (i.e. install the compiled software in a new
          *user image* based on the ``casa-run`` image, where the software is
          installed under ``/casa/install``)
       7. install that user image into  a fresh *user* environment (reference
          test data are automatically linked from the *dev* environment)
       8. perform all tests in that *user* environment

    The process can be controlled with the command-line options described
    below, as well as some configuration keys that can be added to the
    ``casa_distro.json`` of each dev environment:

    - ``ctest_options``: list of command-line options to pass to ``ctest`` on
      the command-line. ``ctest`` is used for listing the tests, so you may
      pass filtering options to restrict the set of tests being run (e.g.
      ``["-R", "disco"]``).

    - ``bbi_user_config``: an optional dictionary for customizing the creation
      of a the user image and the user environment, where tests of the user
      image will be run. This dictionary can contain these keys:

      - ``name``: the name of the environment where the user image will be set
        up. Default: ``dev_config['name'] + '-userimage'``
      - ``directory``: the full path where the user environment will be set up.
        **Warning: this directory is erased every time ``bbi_daily`` is run.**
        Default: ``{{base_directory}} + name``
      - ``image``: the full path where the user image will be created.
        Default: ``{{base_directory}} + name + extension``
      - ``version``: the version string that will be set in the user image,
        e.g. available as the ``CASA_VERSION`` environment variable and as the
        ``version`` metadata key. This value ``version`` is passed to
        :func:`time.strftime`. Default: ``'%Y-%m-%d'``.
      - ``setup_commands``: list of shell commands that will be run in the
        newly created user environment. May be used to run post-setup tasks,
        such as configuring additional files in the home directory of the user
        (e.g. configuring MATLAB licences...).


    Parameters
    ----------
    {distro}
    {branch}
    {system}
    {image_version}
    {name}
    jenkins_server
        default = {jenkins_server_default}
        Base URL of the Jenkins server used to send logs (e.g.
        https://brainvisa.info/builds). If none is given, logs are
        written to standard output.
    jenkins_auth
        default = {jenkins_auth_default}
        Name of a file containing user name and password (can be a token)
        to use to contact Jenkins server REST API. The file must have only
        two lines with login on first line and password on second.
    update_casa_distro
        default = {update_casa_distro_default}
        If true, yes or 1, update casa_distro
    update_base_images
        default = {update_base_images_default}
        Boolean indicating if the update images step must be done
    bv_maker_steps
        default = {bv_maker_steps_default}
        Coma separated list of bv_maker commands to perform on dev
        environments. May be empty to do nothing.
    dev_tests
        default = {dev_tests_default}
        Boolean indicating if the tests must be performed on dev environments
    update_user_images
        default = {update_user_images_default}
        Boolean indicating if images of user environment must be recreated
    recreate_user_envs
        default = {recreate_user_envs_default}
        Boolean indicating if user environments must be wiped and recreated
        using singularity --bind <dir>:/casa/setup ...
    user_tests
        default = {user_tests_default}
        Boolean indicating if the tests must be performed on user environments
    install_thirdparty
        default = {install_thirdparty_default}
        passed to "create_user_image" when update_user_images is true
    {base_directory}
    {verbose}
    '''

    verbose = verbose_file(verbose)
    update_casa_distro = boolean_value(update_casa_distro)
    update_base_images = boolean_value(update_base_images)
    dev_tests = boolean_value(dev_tests)
    update_user_images = boolean_value(update_user_images)
    recreate_user_envs = boolean_value(recreate_user_envs)
    user_tests = boolean_value(user_tests)
    base_directory = os.path.abspath(base_directory)

    # Ensure that all recursively called instances of casa_distro will use
    # the correct base_directory.
    os.environ['CASA_BASE_DIRECTORY'] = base_directory

    if jenkins_server:
        # Import jenkins only if necessary to avoid dependency
        # on requests module
        from casa_distro.jenkins import BrainVISAJenkins

        jenkins_auth = jenkins_auth.format(base_directory=base_directory)
        with open(jenkins_auth) as f:
            jenkins_login, jenkins_password = [i.strip() for i in
                                               f.readlines()[:2]]
        jenkins = BrainVISAJenkins(jenkins_server, jenkins_login,
                                   jenkins_password)
    else:
        jenkins = None
    bbi_daily = BBIDaily(base_directory, jenkins=jenkins)

    if update_casa_distro:
        # Update casa_distro with git and restart with update_casa_distro=no
        success = bbi_daily.update_casa_distro()
        if not success:
            sys.exit('bbi_daily: failed to update casa-distro')
        res = subprocess.call(
            [sys.executable]
            + [i for i in sys.argv if 'update_casa_distro' not in i]
            + ['update_casa_distro=no']
        )
        sys.exit(res)

    successful_tasks = []
    failed_tasks = []
    try:
        # Parse selected environments
        dev_configs = list(iter_environments(base_directory,
                                             type='dev',
                                             distro=distro,
                                             branch=branch,
                                             system=system,
                                             image_version=image_version,
                                             name=name))

        if update_base_images:
            # First, update dev images
            dev_images = set(osp.join(config['directory'], config['image'])
                             for config in dev_configs)
            # Then, download the corresponding run image (iterate on JSONs on
            # the server until we find the run image with the correct uuid)
            # (we must find these images before updating dev images because
            # they may have been removed after that)
            run_images = set(get_run_base_of_dev_image(
                image, url=default_download_url)
                             for image in dev_images)
            success = bbi_daily.update_base_images(dev_images)
            success &= bbi_daily.update_base_images(run_images)

            if success:
                successful_tasks.append('update_base_images')
            else:
                failed_tasks.append('update_base_images')

        if bv_maker_steps:
            bv_maker_steps = bv_maker_steps.split(',')
        for dev_config in dev_configs:
            doc_build_success = False
            if bv_maker_steps:
                successful, failed = bbi_daily.bv_maker(dev_config,
                                                        bv_maker_steps)
                successful_tasks.extend(
                    '{0}: {1}'.format(dev_config['name'], i)
                    for i in successful)
                failed_tasks.extend('{0}: {1}'.format(dev_config['name'], i)
                                    for i in failed)
                if set(failed) - NONFATAL_BV_MAKER_STEPS:
                    # There is no point in running tests and creating a user
                    # image if compilation failed.
                    continue
                doc_build_success = ('doc' in successful)
            if dev_tests:
                successful, failed = bbi_daily.tests(dev_config, dev_config)
                successful_tasks.extend(
                    '{0}: {1}'.format(dev_config['name'], i)
                    for i in successful)
                failed_tasks.extend('{0}: {1}'.format(dev_config['name'], i)
                                    for i in failed)

            # TODO: implement tests in VirtualBox user images
            extension = '.sif'

            user_config = dev_config.get('bbi_user_config', {})
            if 'name' not in user_config:
                user_config['name'] = dev_config['name'] + '-userimage'
            if 'directory' not in user_config:
                user_config['directory'] = os.path.join(base_directory,
                                                        user_config['name'])
            if 'image' not in user_config:
                user_config['image'] = os.path.join(
                    base_directory, user_config['name'] + extension)
            if 'version' not in user_config:
                user_config['version'] = '%Y-%m-%d'
            user_config['version'] = time.strftime(user_config['version'])

            # Wipe the environment before updating the image, because the image
            # may be inside of the user_config['directory'].
            if recreate_user_envs and os.path.exists(user_config['directory']):
                shutil.rmtree(user_config['directory'])

            if update_user_images:
                success = bbi_daily.update_user_image(
                    user_config, dev_config,
                    install_doc=doc_build_success,
                    install_thirdparty=install_thirdparty
                )
                if success:
                    successful_tasks.append('{0}: update user image'.format(
                        user_config['name']))
                else:
                    failed_tasks.append('{0}: update user image'.format(
                        user_config['name']))
                    continue

            if (recreate_user_envs
                    or not os.path.exists(user_config['directory'])):
                success = bbi_daily.recreate_user_env(user_config, dev_config)
                if success:
                    successful_tasks.append('{0}: recreate user env'.format(
                        user_config['name']))
                else:
                    failed_tasks.append('{0}: recreate user env'.format(
                        user_config['name']))
                    continue

            # Reload the full user config from the installed user environment
            user_config = select_environment(
                base_directory, directory=user_config['directory'])

            if user_tests:
                successful, failed = bbi_daily.tests(user_config, dev_config)
                successful_tasks.extend(
                    '{0}: {1}'.format(user_config['name'], i)
                    for i in successful)
                failed_tasks.extend('{0}: {1}'.format(user_config['name'], i)
                                    for i in failed)
    except Exception:
        log = ['Successful tasks']
        log.extend('  - {0}'.format(i) for i in successful_tasks)
        if failed_tasks:
            log .append('Failed tasks')
            log.extend('  - {0}'.format(i) for i in failed_tasks)
        log += ['', 'ERROR:', '', traceback.format_exc()]
        bbi_daily.log(bbi_daily.bbe_name, 'error', 1, '\n'.join(log))
    else:
        log = ['Successful tasks']
        log.extend('  - {0}'.format(i) for i in successful_tasks)
        if failed_tasks:
            log .append('Failed tasks')
            log.extend('  - {0}'.format(i) for i in failed_tasks)
        bbi_daily.log(bbi_daily.bbe_name, 'finished',
                      (1 if failed_tasks else 0), '\n'.join(log))


@command
def local_install(type, action=None, version='*',
                  log_file='/etc/casa_local_install.log',
                  user='brainvisa'):
    '''
    Run the installation procedure to create a run or dev image on the
    local machine. Installation can be don step by step. This command
    is typically used in a VirtualBox machine to debug image creation
    scenario.

    Parameters
    ----------

    type
        Type of image to install. Either "run" or "dev".


    action
        default={action_default}

        If not given, list the possible actions for the selected type and
        indicate if they were done or not. Can have one of the following
        values::

            "next": perform the nex action not already done
            "all": perform all action not already done
            coma separated list of acions:
                perform all selected actions even if they were already done

    version
        default={version_default}

        Image version to use for searching an image builder file. This is
        used as a shell pattern, the default value match any version.

    log_file
        default={log_file_default}

        File where information about steps that have been performed is stored.

    user
        default={user_default}

        Name of the user account to use for non root commands.
    '''
    installer = LocalInstaller(log_file=log_file,
                               user=user)

    for builder_name, steps in installer.log.items():
        for step_name in steps:
            print(builder_name, '/', step_name, 'done')

    pattern = osp.join(osp.dirname(osp.dirname(osp.dirname(
        casa_distro.__file__))),
        'image-recipes', 'casa-{}'.format(type),
        version, 'build_image.py')
    build_files = glob.glob(pattern)
    if not build_files:
        raise ValueError('No file corresponds to pattern {}'.format(pattern))
    elif len(build_files) > 1:
        raise ValueError('Several build files found: {}'.format(
                             ', '.join(build_files)))
    build_file = build_files[0]

    builder = get_image_builder(build_file)
    steps_todo = [i for i in (j.__name__ for j in builder.steps)
                  if i not in installer.log.get(builder.name, {})]

    if not action:
        for step in builder.steps:
            if step.__name__ in installer.log.get(builder.name, {}):
                status = 'done'
            else:
                status = 'to do'
            print(builder.name, '/', step.__name__, status)
        step_names = []
    elif action == 'next':
        step_names = [steps_todo[0]]
    elif action == 'all':
        step_names = steps_todo
    else:
        step_names = ','.split(action)
    for step_name in step_names:
        print('Performing', builder.name, '/', step_name)
        installer.perform_step(build_file, step_name)


@command
def convert_image(source=None,
                  container_type='docker',
                  convert_from=None,
                  verbose=True,
                  **kwargs):
    """Convert a virtual image to another container type

    Parameters
    ----------
    source
        Source image file.

    container_type
        default={container_type_default}

        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker".

    convert_from
        default={convert_from_default}

        Convert from this container type. If not specified, take it from the
        source container metadata.

    {verbose}
    """
    verbose = verbose_file(verbose)

    if container_type not in ('singularity', 'vbox', 'docker'):
        raise ValueError('Unsupported container type: %s' % container_type)

    if container_type == 'docker':
        out_extension = '.docker'
    elif container_type == 'singularity':
        out_extension = '.sif'
    elif container_type == 'vbox':
        out_extension = '.ova'

    if not osp.exists(source):
        base_pattern = osp.expandvars(osp.expanduser(source))
        if verbose:
            print('Looking for source in', base_pattern,
                  file=verbose)
        bases = glob.glob(base_pattern + '.json')
        if len(bases) == 0:
            # Raise appropriate error for non existing file
            open(source)
        elif len(bases) > 1:
            raise ValueError(
                'Several base images found : {0}'.format(', '.join(bases)))
        source = bases[0]

    base = os.path.join(default_base_directory, source)  # make path absolute

    if osp.exists(base + '.json'):
        metadata = json.load(open(base + '.json'))
        if not convert_from:
            convert_from = metadata['container_type']
    else:
        metadata = {}

    if convert_from == 'singularity':
        in_extension = '.sif'
    elif convert_from == 'docker':
        in_extension = '.docker'
    elif convert_from == 'vbox':
        in_extension = '.ova'
    else:
        raise ValueError('Unsupported converted container type: %s'
                         % convert_from)

    output = base
    if base.endswith(in_extension):
        output = base[:-len(in_extension)]
    output += out_extension

    metadata_output = output + '.json'
    metadata['container_type'] = container_type

    if verbose:
        print('Converting', output, file=verbose)
        print('from      ', base, file=verbose)
        pprint(metadata, stream=verbose, indent=4)

    json.dump(metadata, open(metadata_output, 'w'),
              indent=4, separators=(',', ': '))

    if container_type == 'vbox':
        module = casa_distro.vbox
    elif container_type == 'singularity':
        module = casa_distro.singularity
    elif container_type == 'docker':
        module = casa_distro.docker
    else:
        raise ValueError('Unsupported container type: %s' % container_type)

    image_id, msg = module.convert_image(base, metadata, output,
                                         convert_from=convert_from,
                                         verbose=verbose,
                                         **kwargs)
    if msg:
        print(msg)
    elif osp.isfile(output):
        metadata['size'] = os.stat(output).st_size
        metadata['md5'] = file_hash(output)
        metadata['image_id'] = image_id
        json.dump(metadata, open(metadata_output, 'w'),
                  indent=4, separators=(',', ': '))
