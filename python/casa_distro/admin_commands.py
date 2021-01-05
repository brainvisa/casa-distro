# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import datetime
from fnmatch import fnmatchcase
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
import traceback

from casa_distro.command import command, check_boolean
from casa_distro.defaults import (default_base_directory,
                                  default_download_url)
from casa_distro.environment import (BBIDaily,
                                     casa_distro_directory,
                                     iter_environments,
                                     run_container,
                                     select_environment,
                                     update_container_image)
from casa_distro.jenkins import BrainVISAJenkins
from casa_distro.log import verbose_file, boolean_value
import casa_distro.singularity
import casa_distro.vbox
from casa_distro.hash import file_hash
from casa_distro.web import url_listdir


_true_str = re.compile('^(?:yes|true|y|1)$', re.I)
_false_str = re.compile('^(?:no|false|n|0|none)$', re.I)


def str_to_bool(string):
    if _false_str.match(string):
        return False
    if _true_str.match(string):
        return True
    raise ValueError('Invalid value for boolean: ' + repr(string))


@command
def singularity_deb(system,
                    output='singularity-container-{version}-{system}.deb',
                    dockerhub=None,
                    version='3.7.0',
                    go_version='1.15.6'):
    """Create a Debian package to install Singularity.
    Perform the whole installation process from a rw system and Singularity
    source. Then put the result in a *.deb file.

    Parameters
    ----------
    system
        Target system. E.g. ubuntu-20.04

    output
        default={output_default}
        Location of the resulting Debian package file.

    dockerhub
        default=name of the system replacing "-" by ":"
        Name of the base image system to pull from DockerHub.

    base
        Source file use to buld the image. The default value depends on image
        type and container type.

    version
        default={version_default}
        Version of Singularity to use. This must be a valid release version.

    go_version
        default={go_version_default}
        Version of Go language to install during Singularity building process.
        Go language is not included in the final package.
    """

    output = output.format(system=system,
                           version=version)
    if not dockerhub:
        dockerhub = system.replace('-', ':')
    tmp = tempfile.mkdtemp(prefix='singularity-container-deb-')
    try:
        build_sh = osp.join(tmp, 'build.sh')
        open(build_sh, 'w').write('''#!/bin/sh
set -xe
apt update -y
DEBIAN_FRONTEND=noninteractive apt install -y build-essential uuid-dev \
  squashfs-tools libseccomp-dev wget pkg-config git libcryptsetup-dev \
  elfutils rpm alien
cd $TMP
export OS=linux ARCH=amd64
wget https://dl.google.com/go/go$GO_VERSION.$OS-$ARCH.tar.gz
tar -C /usr/local -xzvf go$GO_VERSION.$OS-$ARCH.tar.gz
rm go$GO_VERSION.$OS-$ARCH.tar.gz
export PATH=/usr/local/go/bin:$PATH
export GOPATH="$TMP/cache"
git clone https://github.com/hpcng/singularity.git
cd singularity
git checkout v${SINGULARITY_VERSION}
./mconfig
sed -i 's/Name: singularity/Name: singularity-container/g' \
  singularity.spec
sed -i 's|BuildRoot: /var/tmp/singularity-|BuildRoot: \
/var/tmp/singularity-container-|g' singularity.spec
make -C builddir dist
cd $TMP
mv singularity/singularity-${SINGULARITY_VERSION}.tar.gz \
  singularity/singularity-container-${SINGULARITY_VERSION}.tar.gz
rpmbuild -tb --nodeps \
  singularity/singularity-container-${SINGULARITY_VERSION}.tar.gz
alien --to-deb --scripts \
  $TMP/rpmbuild/RPMS/x86_64/singularity-container-${SINGULARITY_VERSION}-1.x86_64.rpm
mv singularity-container*.deb /tmp/singularity-container-$SYSTEM-x86_64.deb
''')
        tmp_output = '/tmp/singularity-container-{}-x86_64.deb'.format(system)
        subprocess.check_call(['sudo', 'singularity', 'build',
                               '--sandbox', system,
                               'docker://{}'.format(dockerhub)],
                              cwd=tmp)
        subprocess.check_call(['sudo', 'singularity', 'run', '--writable',
                               '--home', tmp,
                               '--env', 'TMP={}'.format(tmp),
                               '--env', 'SYSTEM={}'.format(system),
                               '--env', 'GO_VERSION={}'.format(go_version),
                               '--env',
                               'SINGULARITY_VERSION={}'.format(version),
                               system,
                               'sh', build_sh],
                              cwd=tmp)
        # Use singularity to chown because it may be in sudoers
        subprocess.check_call(['sudo', 'singularity', 'run', system,
                               'chown', '--reference', tmp,
                               tmp_output],
                              cwd=tmp)
        shutil.move(tmp_output, output)
    finally:
        # Use singularity to remove temporary directory because it may be
        # in sudoers
        subprocess.check_call(['sudo', 'singularity', 'run', system,
                               'rm', '-R', tmp],
                              cwd=tmp)


@command
def download_image(type,
                   filename='casa-{type}-*.{extension}',
                   url=default_download_url + '/{container_type}',
                   output=osp.join(
                       default_base_directory, '{filename}'),
                   container_type='singularity',
                   force=False,
                   verbose=True):
    """
    Download an image from brainvisa.info web site

    type
    filename
    url
    output
    container_type
    force
    verbose
    """
    verbose = verbose_file(verbose)

    if type not in ('system', 'run', 'dev'):
        raise ValueError('Unsupported image type: {0}'.format(type))

    if container_type == 'singularity':
        extension = 'sif'
    elif container_type == 'vbox':
        extension = 'vdi'
    else:
        raise ValueError('Unsupported container type: %s' % container_type)

    filename = filename.format(type=type, extension=extension)
    url = url.format(container_type=container_type)
    filenames = [i for i in url_listdir(url)
                 if fnmatchcase(i, filename)]
    if len(filenames) == 0:
        raise ValueError(
            'Cannot find file corresponding to pattern {0} in {1}'
            .format(filename, url)
        )
    elif len(filenames) > 1:
        raise ValueError(
            'Several image files found in {1}: {0}'
            .format(', '.join(filenames), url)
        )
    filename = filenames[0]
    output = output.format(filename=filename)
    output = osp.expandvars(osp.expanduser(output))

    update_container_image(container_type, output, url, force=force,
                           verbose=verbose, new_only=False)


@command
def create_base_image(type,
                      name='casa-{type}-{system}',
                      base=None,
                      output=osp.join(default_base_directory,
                                      '{name}.{extension}'),
                      container_type='singularity',
                      memory='8192',
                      disk_size='131072',
                      gui='no',
                      cleanup='yes',
                      force='no',
                      verbose=True):
    """Create a new virtual image

    Parameters
    ----------
    type
        type of image to create. Either "system" for a base system image, or
        "run" for an image used in a user environment, or "dev" for a developer
        image.

    name
        default={name_default}
        name of the virtual image (no other image must have the same name).

    base
        Source file use to buld the image. The default value depends on image
        type and container type.

    output
        default={output_default}
        File location where the image is created.

    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker".

    memory
        default={memory_default}
        For vbox container type only. Size in MiB of memory allocated for
        virtual machine.

    disk_size
        default={disk_size_default}
        For vbox container type only. Size in MiB of maximum disk size of
        virtual machine.

    gui
        default={gui_default}
        For vbox container type only. If value is "yes", "true" or "1", display
        VirtualBox window.

    cleanup
        default={cleanup_default}

        If "no", "false" or "0", do not cleanup after a failure during image
        building. This may allow to debug a problem after the failure. For
        instance, with Singularity one can use a command like :
          sudo singularity run --writable
          /tmp/rootfs-79744fb2-f3a7-11ea-a080-ce9ed5978945 /bin/bash

    force
        default={force_default}

        If "yes", "true" or 1, erase existing image without asking any
        question.

    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".

    """
    verbose = verbose_file(verbose)
    gui = boolean_value(gui)
    cleanup = boolean_value(cleanup)
    force = boolean_value(force)

    if type not in ('system', 'run', 'dev'):
        raise ValueError('Image type can only be "system", "run" or "dev"')

    if container_type == 'singularity':
        origin_extension = 'sif'
        extension = 'sif'
    elif container_type == 'vbox':
        origin_extension = 'iso'
        extension = 'vdi'
    else:
        raise ValueError('Unsupported container type: %s' % container_type)

    if base is None:
        if type == 'system':
            base = osp.join(
                default_base_directory,
                '*ubuntu-*.{extension}'.format(extension=origin_extension))
        elif type == 'run':
            base = osp.join(
                default_base_directory,
                'casa-system-ubuntu-*.{extension}'.format(extension=extension))
        else:
            base = osp.join(
                default_base_directory,
                'casa-run-ubuntu-*.{extension}'.format(extension=extension))

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

    name = name.format(type=type, system=system)
    output = osp.expandvars(osp.expanduser(output)).format(name=name,
                                                           system=system,
                                                           extension=extension)

    if type == 'system':
        build_file = None
    else:
        share_dir = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))),
                             'share')
        casa_docker = osp.join(share_dir, 'docker', 'casa-%s' % type, system)

        build_file = osp.join(casa_docker, 'build_image.py')
        open(build_file)  # raise appropriate exception if file does not exist

    metadata_output = output + '.json'
    metadata = {
        'name': name,
        'type': type,
        'system': system,
        'container_type': container_type,
        'creation_time': datetime.datetime.now().isoformat(),
    }
    origin = base_metadata.get('origin')
    if origin:
        metadata['origin'] = origin
    elif type == 'system':
        metadata['origin'] = os.path.basename(base)

    if verbose:
        print('Creating', output, file=verbose)
        print('based on', base, file=verbose)
        if build_file:
            print('using', build_file, file=verbose)
        print('metadata = ', end='', file=verbose)
        pprint(metadata, stream=verbose, indent=4)
    json.dump(metadata, open(metadata_output, 'w'), indent=4)

    if container_type == 'vbox':
        module = casa_distro.vbox
    else:
        module = casa_distro.singularity

    msg = module.create_image(base, base_metadata,
                              output, metadata,
                              build_file=build_file,
                              cleanup=cleanup,
                              force=force,
                              verbose=verbose,
                              memory=memory,
                              disk_size=disk_size,
                              gui=gui)
    if msg:
        print(msg)
    elif osp.isfile(output):
        metadata['size'] = os.stat(output).st_size
        metadata['md5'] = file_hash(output)
        json.dump(metadata, open(metadata_output, 'w'), indent=4)


@command
def publish_base_image(type,
                       image=osp.join(
                           default_base_directory,
                           'casa-{type}-*.{extension}'),
                       container_type='singularity',
                       verbose=True):
    """Upload an image to BrainVISA web site.

    Parameters
    ----------

    type
        type of image to publish. Either "system" for a base system image, or
        "run" for an image used in a user environment, or "dev" for a developer
        image.

    image
        default={image_default}
        Image file to upload (as well as the corresponding JSON file)

    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker".

    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".

    """
    verbose = verbose_file(verbose)
    if container_type == 'singularity':
        extension = 'sif'
    elif container_type == 'vbox':
        extension = 'vdi'
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
            raise ValueError(
                'Several image files found : {0}'.format(', '.join(images)))
        image = images[0]

    # Add image file md5 hash to JSON metadata file
    metadata_file = image + '.json'
    metadata = json.load(open(metadata_file))
    metadata['size'] = os.stat(image).st_size
    metadata['md5'] = file_hash(image)
    json.dump(metadata, open(metadata_file, 'w'), indent=4)

    subprocess.check_call(['rsync', '-P', '--progress', '--chmod=a+r',
                           metadata_file, image,
                           'brainvisa@brainvisa.info:prod/www/casa-distro/%s/'
                           % container_type])


@command
def create_user_image(
        version,
        name='{distro}-{version}',
        base_image='{base_directory}/casa-run-{system}{extension}',
        distro=None,
        branch=None,
        system=None,
        environment_name=None,
        container_type=None,
        output=osp.join(
            default_base_directory,
            '{name}{extension}'),
        force='no',
        base_directory=casa_distro_directory(),
        install='yes',
        generate='yes',
        upload='no',
        verbose=True):
    """Create a run image given a development environment.
    The development environment is selected among existing ones its
    distro and system or simply by its name. Only developement environments
    using the master branch are considered.
    This command can perform three steps. Each step can be ignored by setting
    the corresponding option to "no" :

    - install: perform an installation of the development environment into its
      installation directory. This modify the development environment by
      updating its installation directory.

    - generate: generate a new image for the run environment. The ne image is
      based on base_image and the installation directory of the development
      environment is copied into the image in /casa/install.

    - upload: upload the run image on BrainVISA web site.


    Parameters
    ----------
    version
        Version of the release to create.
    name
        default={name_default}
        Name given to the created image.
    base_image
        default={base_image_default}
        Name of the "run" image used to generate the new user image
    distro
        If given, select dev environment having the given distro name.
    branch
        If given, select dev environment having the given branch name.
    system
        If given, select dev environments having the given system name.
    environment_name
        If given, select dev environment by its name.
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker".
    force
        default={force_default}
        If "yes", "true" or 1, erase existing image without asking any
        question.
    base_directory
        default={base_directory_default}
        Directory where images and environments are stored
    install
        default={install_default}
        If "true", "yes" or "1", perform the installation step.
        If "false", "no" or "0", skip this step
    generate
        default={generate_default}
        If "true", "yes" or "1", perform the image creation step.
        If "false", "no" or "0", skip this step
    upload
        default={upload_default}
        If "true", "yes" or "1", upload the image on BrainVISA web site.
        If "false", "no" or "0", skip this step
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".

    """
    install = check_boolean('install', install)
    generate = check_boolean('generate', generate)
    upload = check_boolean('upload', upload)

    verbose = verbose_file(verbose)
    config = select_environment(base_directory,
                                type='dev',
                                distro=distro,
                                branch=branch,
                                system=system,
                                name=environment_name,
                                container_type=container_type)
    container_type = config['container_type']
    if container_type == 'singularity':
        extension = '.sif'
        module = casa_distro.singularity
    elif container_type == 'vbox':
        extension = '.vdi'
        module = casa_distro.vbox
    else:
        raise ValueError('Unsupported container type: {0}'.format(
            container_type))
    name = name.format(version=version, **config)
    kwargs = config.copy()
    kwargs.pop('name', None)
    output = osp.expandvars(osp.expanduser(output)).format(name=name,
                                                           extension=extension,
                                                           **kwargs)
    force = boolean_value(force)

    metadata = {
        'name': name,
        'type': 'run',
        'distro': config['distro'],
        'system': config['system'],
        'version': version,
        'container_type': container_type,
        'creation_time': datetime.datetime.now().isoformat(),
    }
    base_image = base_image.format(base_directory=base_directory,
                                   extension=extension,
                                   **metadata)

    if install:
        # TODO check the return code
        try:
            # determine cpu count
            import joblib  # might not be installed
            cpu_opt = ['-j%d' % joblib.cpu_count()]
        except ImportError:
            cpu_opt = []
        # make install-runtime hangs somewhere when used with parallel options
        run_container(config=config,
                      command=['make',
                               'BRAINVISA_INSTALL_PREFIX=/casa/host/install',
                               'install-runtime'],  # + cpu_opt,
                      gui=False,
                      opengl="auto",
                      root=False,
                      cwd='/casa/host/build',
                      env={},
                      image=None,
                      container_options=None,
                      base_directory=base_directory,
                      verbose=verbose)
        run_container(config=config,
                      command=['make',
                               'BRAINVISA_INSTALL_PREFIX=/casa/host/install',
                               'install-doc'] + cpu_opt,
                      gui=False,
                      opengl="auto",
                      root=False,
                      cwd='/casa/host/build',
                      env={},
                      image=None,
                      container_options=None,
                      base_directory=base_directory,
                      verbose=verbose)
        run_container(config=config,
                      command=['make',
                               'BRAINVISA_INSTALL_PREFIX=/casa/host/install',
                               'install-test'] + cpu_opt,
                      gui=False,
                      opengl="auto",
                      root=False,
                      cwd='/casa/host/build',
                      env={},
                      image=None,
                      container_options=None,
                      base_directory=base_directory,
                      verbose=verbose)

    metadata_file = output + '.json'

    if generate:
        output_dir = osp.dirname(output)
        if not osp.exists(output_dir):
            os.makedirs(output_dir)
        msg = module.create_user_image(base_image=base_image,
                                       dev_config=config,
                                       output=output,
                                       force=force,
                                       base_directory=base_directory,
                                       verbose=verbose)
        if msg:
            print(msg)

        # Add image file md5 hash to JSON metadata file
        metadata['size'] = os.stat(output).st_size
        metadata['md5'] = file_hash(output)
        json.dump(metadata, open(metadata_file, 'w'), indent=4)

    if upload:
        url = 'brainvisa@brainvisa.info:prod/www/casa-distro/releases/' \
            '{container_type}'.format(**metadata)
        subprocess.check_call(['rsync', '-P', '--progress', '--chmod=a+r',
                               metadata_file, output, url])


@command
def bbi_daily(type=None, distro=None, branch=None, system=None, name=None,
              version=None,
              jenkins_server=None,
              jenkins_auth='{base_directory}/jenkins_auth',
              jenkins_password=None,
              update_casa_distro='yes',
              update_base_images='yes',
              bv_maker_steps='sources,configure,build,doc',
              dev_tests='yes',
              update_user_images='yes',
              user_tests='yes',
              base_directory=casa_distro_directory(),
              verbose=None):
    '''
    In BrainVISA Build Infrastructure (BBI), there are be some machines
    that are be targeted to do some builds and tests. This command is
    used to perform these tasks and is be typically used in a crontab
    on each machine. It does the following things (and log progress and
    results in Jenkins server) :

    - Update casa_distro to latest master version and restart for the next
      steps
    - Parse all configured environments selected with a filter as with mrun
      command
    - Update dev and run images used by selected environments from BrainVISA
      site
    - For all selected dev environments, perform the following tasks :
        - bv_maker sources
        - bv_maker configure
        - bv_maker build
        - bv_maker doc
        - perform all tests (as bv_maker test)
    - For all selected user environments
        - find the corresponding dev environment
        - recreate the user environment image with casa_distro_admin
          create_user_image
        - perform all tests defined in the correponding dev environment
          but execute them in the user environment


    Parameters
    ----------
    {type}
    {distro}
    {branch}
    {system}
    {name}
    {version}
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
    user_tests
        default = {user_tests_default}
        Boolean indicating if the tests must be performed on user environments
    {base_directory}
    {verbose}
    '''

    verbose = verbose_file(verbose)
    update_casa_distro = boolean_value(update_casa_distro)
    update_base_images = boolean_value(update_base_images)
    dev_tests = boolean_value(dev_tests)
    update_user_images = boolean_value(update_user_images)
    user_tests = boolean_value(user_tests)

    if jenkins_server:
        jenkins_auth = jenkins_auth.format(base_directory=base_directory)
        jenkins_login, jenkins_password = [i.strip() for i in
                                           open(jenkins_auth).readlines()[:2]]
        jenkins = BrainVISAJenkins(jenkins_server, jenkins_login,
                                   jenkins_password)
    else:
        jenkins = None
    bbi_daily = BBIDaily(jenkins=jenkins)

    if update_casa_distro:
        # Update casa_distro with git and restart with update_casa_distro=no
        bbi_daily.update_casa_distro()
        res = subprocess.call([i for i in sys.argv
                               if 'update_casa_distro' not in i]
                              + ['update_casa_distro=no'])
        sys.exit(res)

    succesful_tasks = []
    failed_tasks = []
    try:

        # Parse selected environments
        dev_configs = {}
        run_configs = []
        images = set()
        for config in iter_environments(base_directory,
                                        type=type,
                                        distro=distro,
                                        branch=branch,
                                        system=system,
                                        name=name,
                                        version=version):
            if config['type'] == 'dev':
                key = (config['distro'], config['branch'], config['system'])
                if key in dev_configs:
                    raise RuntimeError('Several dev environment found for '
                                       'distro={0}, branch={1} and '
                                       'system={1}'.format(*key))
                dev_configs[key] = config
                images.add(config['image'])
            elif config['type'] == 'run':
                run_configs.append(config)
                images.add(config['image'])

        # Associate run environments to corresponding dev environment
        for i in range(len(run_configs)):
            config = run_configs[i]
            key = (config['distro'], u'master', config['system'])
            dev_config = dev_configs.get(key)
            if dev_config is None:
                raise RuntimeError('No dev environment found for '
                                   'distro={0}, branch={1} and '
                                   'system={1}'.format(*key))
            run_configs[i] = (config, dev_config)
        dev_configs = list(dev_configs.values())

        if update_base_images:
            if bbi_daily.update_base_images(images):
                succesful_tasks.append('update_base_images')
            else:
                failed_tasks.append('update_base_images')

        failed_dev_configs = set()
        if bv_maker_steps:
            bv_maker_steps = bv_maker_steps.split(',')
        for config in dev_configs:
            failed = None
            if bv_maker_steps:
                succesful, failed = bbi_daily.bv_maker(config, bv_maker_steps)
                succesful_tasks.extend('{0}: {1}'.format(config['name'], i)
                                       for i in succesful)
                if failed:
                    failed_tasks.append('{0}: {1}'.format(config['name'],
                                                          failed))
                if failed:
                    failed_dev_configs.add(config['name'])
                    continue
            if dev_tests:
                succesful, failed = bbi_daily.tests(config, config)
                succesful_tasks.extend('{0}: {1}'.format(config['name'], i)
                                       for i in succesful)
                failed_tasks.extend('{0}: {1}'.format(config['name'], i)
                                    for i in failed)
                if failed:
                    failed_dev_configs.add(config['name'])
                    continue

        for config, dev_config in run_configs:
            if dev_config['name'] in failed_dev_configs:
                continue
            if update_user_images:
                if bbi_daily.update_user_image(config, dev_config):
                    succesful_tasks.append('{0}: update user image'.format(
                        config['name']))
                else:
                    failed_tasks.append('{0}: update user image'.format(
                        config['name']))
                    continue
            if user_tests:
                succesful, failed = bbi_daily.tests(config, dev_config)
                succesful_tasks.extend('{0}: {1}'.format(config['name'], i)
                                       for i in succesful)
                failed_tasks.extend('{0}: {1}'.format(config['name'], i)
                                    for i in failed)
                if failed:
                    continue
    except Exception:
        log = ['Succesful tasks']
        log.extend('  - {0}'.format(i) for i in succesful_tasks)
        if failed_tasks:
            log .append('Failed tasks')
            log.extend('  - {0}'.format(i) for i in failed_tasks)
        log += ['', 'ERROR:', '', traceback.format_exc()]
        bbi_daily.log(bbi_daily.bbe_name, 'error', 1, '\n'.join(log))
    else:
        log = ['Succesful tasks']
        log.extend('  - {0}'.format(i) for i in succesful_tasks)
        if failed_tasks:
            log .append('Failed tasks')
            log.extend('  - {0}'.format(i) for i in failed_tasks)
        bbi_daily.log(bbi_daily.bbe_name, 'finished',
                      (1 if failed_tasks else 0), '\n'.join(log))
