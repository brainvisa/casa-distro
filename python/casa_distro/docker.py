# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os
import os.path as osp
import re
import shutil
import subprocess
from subprocess import check_call, check_output, call
import sys
import tempfile

from casa_distro import six
from casa_distro.log import verbose_file
import casa_distro.info
from casa_distro import share_directories


def get_docker_version():
    dverout = check_output(['docker', '-v'])
    if not isinstance(dverout, str):
        dverout = dverout.decode()  # Python 3
    r = re.match('Docker version ([0-9.]+).*$', dverout)
    return [int(x) for x in r.group(1).split('.')]


def find_docker_image_files():
    '''
    Return a sorted list of dictionary corresponding to the content of
    all the "casa_distro_docker.yaml" files located in given directory.
    The result is sorted according to the dependencies declared in the files.
    '''
    import yaml

    result = []
    dependencies = {}

    share_dirs = share_directories()
    base_dirs = [osp.abspath(osp.normpath(osp.join(share_directory, 'docker')))
                 for share_directory in share_dirs]

    for sh_id, share_directory in enumerate(share_dirs):
        base_directory = base_dirs[sh_id]
        for root, dirnames, filenames in os.walk(base_directory):
            if 'casa_distro_docker.yaml' in filenames:
                yaml_filename = osp.normpath(
                    osp.join(root, 'casa_distro_docker.yaml'))
                rel_root = osp.relpath(root, base_directory)
                images_dict = yaml.load(open(yaml_filename))
                images_dict['filename'] = yaml_filename
                deps = images_dict.get('dependencies')
                if deps:
                    for dependency in deps:
                        # look for files in all docker base dirs
                        for test_basedir in base_dirs:
                            test_root = osp.join(test_basedir, rel_root)
                            for r, d, f in os.walk(
                                    osp.normpath(osp.join(test_root,
                                                          dependency))):
                                if 'casa_distro_docker.yaml' in f:
                                    dependencies.setdefault(
                                        yaml_filename,
                                        set()).add(osp.normpath(
                                            osp.join(
                                                r,
                                                'casa_distro_docker.yaml')))
                result.append(images_dict)

        propagate_dependencies = True
        while propagate_dependencies:
            propagate_dependencies = False
            for i, d in dependencies.items():
                for j in tuple(d):
                    for k in dependencies.get(j, ()):
                        i_deps = dependencies.setdefault(i, set())
                        if k not in i_deps:
                            i_deps.add(k)
                            propagate_dependencies = True

        def compare_with_dependencies(a, b):
            if a['filename'] == b['filename']:
                return 0
            elif a['filename'] in dependencies.get(b['filename'], ()):
                return -1
            elif b['filename'] in dependencies.get(a['filename'], ()):
                return 1
            else:
                if a['filename'] == b['filename']:
                    return 0
                elif a['filename'] < b['filename']:
                    return -1
                else:
                    return 1
                # return cmp(a['filename'], b['filename'])

        def cmp_to_key(mycmp):
            'Convert a cmp= function into a key= function'
            class K(object):

                def __init__(self, obj, *args):
                    self.obj = obj

                def __lt__(self, other):
                    return mycmp(self.obj, other.obj) < 0

                def __gt__(self, other):
                    return mycmp(self.obj, other.obj) > 0

                def __eq__(self, other):
                    return mycmp(self.obj, other.obj) == 0

                def __le__(self, other):
                    return mycmp(self.obj, other.obj) <= 0

                def __ge__(self, other):
                    return mycmp(self.obj, other.obj) >= 0

                def __ne__(self, other):
                    return mycmp(self.obj, other.obj) != 0
            return K

    return sorted(result, key=cmp_to_key(compare_with_dependencies))


def apply_template_parameters(template, template_parameters):
    while True:
        result = template % template_parameters
        if result == template:
            break
        template = result
    return result


def image_name_match(image_name, filters):
    '''
    Tests if an image name matches one of the filters.
    It uses fnmatch syntax.
    '''
    import fnmatch

    for f in filters:
        if fnmatch.fnmatch(image_name, f):
            return True

    return False


def update_docker_images(image_name_filters=['*']):
    image_file_count = 0
    for images_dict in find_docker_image_files():
        for image_source in images_dict['image_sources']:
            template_parameters = {
                'casa_version': casa_distro.info.__version__}
            template_parameters.update(
                image_source.get('template_files_parameters', {}))

            image_name = apply_template_parameters(
                image_source['name'], template_parameters)

            image_tags = [apply_template_parameters(i, template_parameters)
                          for i in image_source['tags']]
            tag = image_tags[-1]
            image_full_name = 'cati/%s:%s' % (image_name, tag)
            if not image_name_match(image_full_name, image_name_filters):
                continue
            image_file_count += 1
            cmd = ['docker', 'pull', image_full_name]
            print('-' * 70)
            print(*cmd)
            print('-' * 70)
            call(cmd)
    return image_file_count


def get_image_id(image_full_name):
    try:
        images = check_output(['docker', 'images', image_full_name])
    except subprocess.CalledProcessError:
        return None
    images = [i for i in images.split('\n')[1:] if i != '']
    if len(images) != 1:
        return None
    image_id = images[0].split()[2]
    return image_id


def get_base_image(dockerfile):
    with open(dockerfile) as f:
        while f:
            line = f.readline().strip()
            if line == '':
                continue
            el = line.split()
            if len(el) == 0 or el[0] != 'FROM':
                continue
            return el[1]


def pull_image(image_full_name):
    cmd = ['docker', 'pull', image_full_name]
    print('-' * 70)
    print(*cmd)
    print('-' * 70)
    old_image = get_image_id(image_full_name)
    try:
        check_call(cmd)
        if get_image_id(image_full_name) != old_image:
            return old_image
    except subprocess.CalledProcessError:
        return None
    return None


def rm_images(images):
    if len(images) == 0:
        return
    cmd = ['docker', 'rmi'] + images
    print('-' * 70)
    print(*cmd)
    print('-' * 70)
    tmp = tempfile.mkstemp()
    try:
        call(cmd, stderr=open(tmp[1], 'w'))
    finally:
        try:
            os.close(tmp[0])
        except OSError:
            pass
        try:
            os.unlink(tmp[1])
        except OSError:
            pass


def create_docker_images(image_name_filters=['*'],
                         no_host_network=False):
    '''
    Creates all docker images that are declared in
    find_docker_image_files().
    Return the number of images processed.

    This function is still work in progress. Its parameters and behaviour may
    change.


    '''
    image_file_count = 0
    to_clean = []
    try:
        for images_dict in find_docker_image_files():
            base_directory = tempfile.mkdtemp()
            try:
                source_directory, filename = osp.split(images_dict['filename'])
                for image_source in images_dict['image_sources']:
                    template_parameters = {
                        'casa_version': casa_distro.info.__version__}
                    template_parameters.update(
                        image_source.get('template_files_parameters', {}))

                    image_name = apply_template_parameters(
                        image_source['name'], template_parameters)

                    image_tags = [
                        apply_template_parameters(i, template_parameters)
                        for i in image_source['tags']]
                    target_directory = osp.join(
                        base_directory, image_name, image_tags[-1])
                    os.makedirs(target_directory)
                    for f in os.listdir(source_directory):
                        if f == filename:
                            continue
                        source = osp.join(source_directory, f)
                        target = osp.join(target_directory, f)

                        if osp.isdir(source):
                            if os.path.exists(target):
                                shutil.rmtree(target)
                            shutil.copytree(source, target)
                        elif f.endswith('.template'):
                            content = apply_template_parameters(
                                open(source).read(),
                                template_parameters
                            )
                            open(target[:-9], 'w').write(content)
                        else:
                            shutil.copy2(source, target)

                    image_full_name = 'cati/%s:%s' % (
                        image_name, image_tags[-1])

                    if not image_name_match(image_full_name,
                                            image_name_filters):
                        continue
                    image_file_count += 1

                    old_id = get_image_id(image_full_name)
                    old_base_id = None
                    deps = images_dict.get('dependencies', [])
                    if len(deps) == 0:
                        base_image = get_base_image(
                            os.path.join(target_directory, 'Dockerfile'))
                        if base_image:
                            old_base_id = pull_image(base_image)

                    docker_ver = get_docker_version()
                    # Docker 1.13 adds the --network option to build commands.
                    # This is useful to avoid a DNS (/etc/resolv.conf) problem
                    # happening on many Ubuntu computers where the host
                    # /etc/resolv.conf uses 127.0.0.1 Unfortunately it is not
                    # available in older releases of docker, including
                    # those shipped in Ubuntu 16.04 (which is 1.12).
                    if not no_host_network and docker_ver >= [1, 13]:
                        cmd = ['docker', 'build', '--network=host']
                    else:
                        cmd = ['docker', 'build']
                    cmd += ['--force-rm', '--tag', image_full_name,
                            target_directory]
                    print('-' * 40)
                    print('Creating image %s' % image_full_name)
                    print(*cmd)
                    print('Docker context:', os.listdir(target_directory))
                    print('-' * 40)
                    check_call(cmd)
                    if old_id is not None \
                            and get_image_id(image_full_name) != old_id:
                        to_clean.append(old_id)
                    if old_base_id:
                        to_clean.append(old_base_id)
                    print('-' * 40)
                    for tag in image_tags[:-1]:
                        src = 'cati/%s:%s' % (image_name, image_tags[-1])
                        dst = 'cati/%s:%s' % (image_name, tag)
                        print('Creating tag', dst, 'from', src)
                        # I do not know how to create a tag of an existing
                        # image with docker-py, therefore I use subprocess
                        check_call(['docker', 'tag', src, dst])
                    print('-' * 40)
            finally:
                shutil.rmtree(base_directory)
    finally:
        rm_images(to_clean)
    return image_file_count


def publish_docker_images(image_name_filters=['*']):
    '''
    Publish, on DockerHub, all docker images that are declared in
    find_docker_image_files().
    Return the number of images processed.

    This function is still work in progress. Its parameters and behaviour may
    change.
    '''
    import casa_distro

    image_file_count = 0
    for images_dict in find_docker_image_files():
        source_directory, filename = osp.split(images_dict['filename'])
        for image_source in images_dict['image_sources']:
            template_parameters = {
                'casa_version': casa_distro.info.__version__}
            template_parameters.update(
                image_source.get('template_files_parameters', {}))

            image_name = apply_template_parameters(
                image_source['name'], template_parameters)

            image_tags = [apply_template_parameters(i, template_parameters)
                          for i in image_source['tags']]
            for tag in image_tags:
                image_full_name = 'cati/%s:%s' % (image_name, tag)
                if not image_name_match(image_full_name, image_name_filters):
                    continue
                image_file_count += 1
                print('-' * 70)
                print('pushing image:', image_full_name)
                check_call(['docker', 'push', image_full_name])
    return image_file_count


def update_docker_image(container_image):
    '''
    Update a docker image.
    '''
    check_call(['docker', 'pull', container_image])


def run_docker(casa_distro, command, gui=False, interactive=False,
               tmp_container=True, container_image=None, cwd=None, env=None,
               container_options=[],
               verbose=None):
    """Run a command in the Docker container.

    Return the exit code of the command, or raise an exception if the command
    cannot be run.
    """
    verbose = verbose_file(verbose)

    docker = ['docker', 'run']
    if interactive:
        docker += ['-it']
    if tmp_container:
        docker += ['--rm']
    if cwd:
        docker += ['-w', cwd]
    if gui:
        gui_options = casa_distro.get('container_gui_options')
        if gui_options:
            docker += [osp.expandvars(i) for i in gui_options]
    # could add options for gdb:
    # docker += ['--security-opt', 'seccomp=unconfined']
    for dest, source in six.iteritems(casa_distro.get('container_mounts', {})):
        source = source % casa_distro
        source = osp.expandvars(source)
        dest = dest % casa_distro
        dest = osp.expandvars(dest)
        docker += ['-v', '%s:%s' % (source, dest)]
    container_env = dict(casa_distro.get('container_env', {}))
    if gui:
        container_env.update(casa_distro.get('container_gui_env', {}))
    if env is not None:
        container_env.update(env)
    for name, value in six.iteritems(container_env):
        value = value % casa_distro
        value = osp.expandvars(value)
        docker += ['-e', '%s=%s' % (name, value)]
    docker += casa_distro.get('container_options', [])
    docker += container_options
    if container_image is None:
        container_image = casa_distro.get('container_image')
        if container_image is None:
            raise ValueError(
                'container_image is missing from casa_distro.json')
    docker += [container_image]
    docker += command
    if verbose:
        print('-' * 40, file=verbose)
        print('Running docker with the following command:', file=verbose)
        print(*("'%s'" % i for i in docker), file=verbose)
        print('-' * 40, file=verbose)
    return subprocess.call(docker)


def create_image(base, base_metadata,
                 output, metadata,
                 image_builder,
                 cleanup='yes',
                 force='no',
                 fakeroot='yes',
                 verbose=None):

    raise NotImplementedError(
        'create_image for docker is not implemented yet.')


def convert_image(source, metadata, output, convert_from, verbose=None):
    if convert_from == 'singularity':
        return convert_singularity_image_to_docker(source, metadata, output,
                                                   verbose=verbose)
    else:
        raise NotImplementedError(
            'Currently converting to docker images is only supported from '
            'singularity.')


def convert_singularity_image_to_docker(base, metadata,
                                        output,
                                        verbose=None):

    # converting singularity images to docker:
    # see https://stackoverflow.com/questions/60451712/
    #     how-to-build-docker-image-from-singularity-image

    # Find out which SIF ID to use (look for Squashfs)
    cmd = ['singularity', 'sif', 'list', base]
    sif_out = subprocess.check_output(cmd).split('\n')

    n = 0
    for i, line in enumerate(sif_out):
        if line.startswith('--------'):
            n = i

    sif_content = []
    squashfs_id = None
    for line in sif_out[n+1:]:
        fields = [x.strip() for x in line.split('|')]
        if len(fields) >= 5:
            num = int(fields[0])
            group = int(fields[1])
            sif_content.append([num, group] + fields[2:])
            stype = fields[4]
            if 'Squashfs' in stype:
                squashfs_id = num

    if squashfs_id is None:
        raise ValueError('squashfs not found in singularity image')

    # Get the environment variables defined in the Singularity image.
    # singularity sif dump 2 alpine_latest.sif

    # use a temp dir to work
    base = osp.abspath(base)
    stmpd = os.environ.get('SINGULARITY_TMPDIR')
    tmp_dir = tempfile.mkdtemp(prefix='singularity_docker_', dir=stmpd)
    print('converting in temp directory:', tmp_dir)
    cwd = os.getcwd()
    os.chdir(tmp_dir)
    try:
        # Get the squashfs dump

        cmd = ['sh', '-c',
               'singularity sif dump %d %s > data.squash'
               % (squashfs_id, base)]
        subprocess.check_call(cmd)
        cmd = ['unsquashfs', '-dest', 'data', 'data.squash']
        subprocess.check_call(cmd)

        # write the Dockerfile definition

        with open('Dockerfile', 'w') as f:
            f.write('''FROM scratch
COPY data /
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENTRYPOINT ["/.singularity.d/runscript"]
CMD ["/bin/bash"]
''')

        image_tag = metadata['name']
        image_version = metadata['image_version']
        if image_tag.endswith('-%s' % metadata['image_version']):
            image_tag = image_tag[:-(len(image_version) + 1)]
        image_tag += ':%s' % image_version
        print('image_tag:', image_tag)

        cmd = ['docker', 'build', '--tag', image_tag, '.']
        subprocess.check_call(cmd)

        return (get_image_id(image_tag), None)

    finally:
        os.chdir(cwd)
        if osp.exists(tmp_dir):
            shutil.rmtree(tmp_dir)


if __name__ == '__main__':
    import casa_distro.docker

    function = getattr(casa_distro.docker, sys.argv[1])
    args = []
    kwargs = {}
    for i in sys.argv[2:]:
        lst = i.split('=', 1)
        if len(lst) == 2:
            kwargs[lst[0]] = lst[1]
        else:
            args.append(i)
    function(*args, **kwargs)
