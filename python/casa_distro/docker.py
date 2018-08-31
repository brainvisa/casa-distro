# coding: utf-8 

from __future__ import absolute_import
from __future__ import print_function

import errno
import json
import os
import os.path as osp
import shutil
from subprocess import check_call, check_output, call
import sys
import tempfile
import stat
import re

from casa_distro import log, six
import casa_distro.info
from casa_distro import share_directory, linux_os_ids



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
    The result is sorted according to the depencies declared in the files.
    '''
    import yaml
    
    base_directory = osp.join(share_directory, 'docker')
    result = []
    dependencies = {}
    base_directory = osp.abspath(osp.normpath(base_directory))
    for root, dirnames, filenames in os.walk(base_directory):
        if 'casa_distro_docker.yaml' in filenames:
            yaml_filename = osp.normpath(osp.join(root, 'casa_distro_docker.yaml'))
            images_dict = yaml.load(open(yaml_filename))
            images_dict['filename'] = yaml_filename
            deps = images_dict.get('dependencies')
            if deps:
                for dependency in deps:
                    for r, d, f in os.walk(osp.join(root, dependency)):
                        if 'casa_distro_docker.yaml' in f:
                            dependencies.setdefault(yaml_filename, set()).add(osp.normpath(osp.join(r, 'casa_distro_docker.yaml')))
            result.append(images_dict)

    propagate_dependencies = True
    while propagate_dependencies:
        propagate_dependencies = False
        for i, d in dependencies.items():
            for j in tuple(d):
                for k in dependencies.get(j,()):
                    i_deps = dependencies.setdefault(i, set())
                    if k not in i_deps:
                        i_deps.add(k)
                        propagate_dependencies = True
                        
    def compare_with_dependencies(a,b):
        if a['filename'] == b['filename']:
            return 0
        elif a['filename'] in dependencies.get(b['filename'],()):
            return -1
        elif b['filename'] in dependencies.get(a['filename'],()):
            return 1
        else:
            return cmp(a['filename'], b['filename'])
    
    return sorted(result, compare_with_dependencies)


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

def update_docker_images(image_name_filters = ['*']):
    image_file_count = 0
    for images_dict in find_docker_image_files():
        for image_source in images_dict['image_sources']:
            template_parameters = { 'casa_version': casa_distro.info.__version__ }
            template_parameters.update(image_source.get('template_files_parameters', {}))
            
            image_name = apply_template_parameters(image_source['name'], template_parameters)
            
            image_tags = [apply_template_parameters(i, template_parameters) for i in image_source['tags']]
            tag = image_tags[-1]
            image_full_name = 'cati/%s:%s' % (image_name, tag)
            if not image_name_match(image_full_name, image_name_filters):
                continue
            image_file_count += 1
            cmd = ['docker', 'pull', image_full_name]
            print('-'*70)
            print(*cmd)
            print('-'*70)
            call(cmd)
    return image_file_count

def get_image_id(image_full_name):
    try:
        images = check_output(['docker', 'images', image_full_name])
    except:
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
    print('-'*70)
    print(*cmd)
    print('-'*70)
    old_image = get_image_id(image_full_name)
    try:
        check_call(cmd)
        if get_image_id(image_full_name) != old_image:
            return old_image
    except:
        return None
    return None

def rm_images(images):
    if len(images) == 0:
        return
    cmd = ['docker', 'rmi'] + images
    print('-'*70)
    print(*cmd)
    print('-'*70)
    tmp = tempfile.mkstemp()
    try:
        call(cmd, stderr=open(tmp[1], 'w'))
    finally:
        try:
            os.close(tmp[0])
        except:
            pass
        try:
            os.unlink(tmp[1])
        except:
            pass

def create_docker_images(image_name_filters = ['*']):
    '''
    Creates all docker images that are declared in 
    find_docker_image_files().
    Return the number of images processed.
    
    This function is still work in progress. Its paramaters and behaviour may
    change.
    
    
    ''' 
    image_file_count = 0
    error = False
    to_clean = []
    try:
        for images_dict in find_docker_image_files():
            base_directory = tempfile.mkdtemp()
            try:
                source_directory, filename = osp.split(images_dict['filename'])
                for image_source in images_dict['image_sources']:
                    template_parameters = { 'casa_version': casa_distro.info.__version__ }
                    template_parameters.update(image_source.get('template_files_parameters', {}))

                    image_name = apply_template_parameters(image_source['name'], template_parameters)

                    image_tags = [apply_template_parameters(i, template_parameters) for i in image_source['tags']]
                    target_directory = osp.join(base_directory, image_name, image_tags[-1])
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
                            content = apply_template_parameters(open(source).read(), template_parameters)
                            open(target[:-9], 'w').write(content)
                        else:
                            shutil.copy2(source, target)

                    image_full_name = 'cati/%s:%s' % (image_name, image_tags[-1])

                    if not image_name_match(image_full_name, image_name_filters):
                        continue
                    image_file_count += 1

                    old_id = get_image_id(image_full_name)
                    old_base_id = None
                    deps = images_dict.get('dependencies', [])
                    if len(deps) == 0:
                        base_image = get_base_image(os.path.join(target_directory,
                                                                'Dockerfile'))
                        if base_image:
                            old_base_id = pull_image(base_image)

                    cmd = ['docker', 'build', '--force-rm',
                           '--tag', image_full_name, target_directory]
                    print('-'*40)
                    print('Creating image %s' % image_full_name)
                    print(*cmd)
                    print('Docker context:', os.listdir(target_directory))
                    print('-'*40)
                    check_call(cmd)
                    if get_image_id(image_full_name) != old_id:
                        to_clean.append(old_id)
                    if old_base_id:
                        to_clean.append(old_base_id)
                    print('-'*40)
                    for tag in image_tags[:-1]:
                        src = 'cati/%s:%s' % (image_name, image_tags[-1])
                        dst = 'cati/%s:%s' % (image_name, tag)
                        print('Creating tag', dst, 'from', src)
                        # I do not know how to create a tag of an existing image with
                        # docker-py, therefore I use subprocess
                        check_call(['docker', 'tag', src, dst] )
                    print('-'*40)
                if error:
                    break
            finally:
                shutil.rmtree(base_directory)
    finally:
        rm_images(to_clean)
    return image_file_count


def publish_docker_images(image_name_filters = ['*']):
    '''
    Publish, on DockerHub, all docker images that are declared in 
    find_docker_image_files().
    Return the number of images processed.
    
    This function is still work in progress. Its paramaters and behaviour may
    change.
    '''
    import casa_distro
    
    image_file_count = 0
    for images_dict in find_docker_image_files():
        base_directory = tempfile.mkdtemp()
        source_directory, filename = osp.split(images_dict['filename'])
        for image_source in images_dict['image_sources']:
            template_parameters = { 'casa_version': casa_distro.info.__version__ }
            template_parameters.update(image_source.get('template_files_parameters', {}))
            
            image_name = apply_template_parameters(image_source['name'], template_parameters)
                
            image_tags = [apply_template_parameters(i, template_parameters) for i in image_source['tags']]
            for tag in image_tags:
                image_full_name = 'cati/%s:%s' % (image_name, tag)
                if not image_name_match(image_full_name, image_name_filters):
                    continue
                image_file_count += 1
                print('-'*70)
                print('pushing image:', image_full_name)
                check_call(['docker', 'push', image_full_name])
    return image_file_count


def update_docker_image(container_image):
    '''
    Update a docker image.
    '''
    check_call(['docker', 'pull', container_image])


def run_docker(casa_distro, command, gui=False, interactive=False,
               tmp_container=True, container_image=None, container_options=[],
               verbose=None):
    
    verbose = log.getLogFile(verbose)
    
    docker = ['docker', 'run']
    if interactive:
        docker += ['-it']
    if tmp_container:
        docker += ['--rm']
    if gui:
        gui_options = casa_distro.get('container_gui_options')
        if gui_options:
            docker += [osp.expandvars(i) for i in gui_options]
    # could add options for gdb:
    # docker += ['--security-opt', 'seccomp=unconfined']
    for source, dest in six.iteritems(casa_distro.get('container_volumes',{})):
        source = source % casa_distro
        source = osp.expandvars(source)
        dest = dest % casa_distro
        dest = osp.expandvars(dest)
        docker += ['-v', '%s:%s' % (source, dest)]
    container_env = casa_distro.get('container_env',{})
    if gui:
        container_env.update(casa_distro.get('container_gui_env',{}))
    for name, value in six.iteritems(container_env):
        value = value % casa_distro
        value = osp.expandvars(value)
        docker += ['-e', '%s=%s' % (name, value)]
    docker += casa_distro.get('container_options', [])
    docker += container_options
    if container_image is None:
        container_image = casa_distro.get('container_image')
        if container_image is None:
            raise ValueError('container_image is missing from casa_distro.json')
    docker += [container_image]
    docker += command
    if verbose:
        print('-' * 40, file=verbose)
        print('Running docker with the following command:', file=verbose)
        print(*("'%s'" % i for i in docker), file=verbose)
        print('-' * 40, file=verbose)
    check_call(docker)



if __name__ == '__main__':
    import sys
    import casa_distro.docker

    function = getattr(casa_distro.docker, sys.argv[1])
    args=[]
    kwargs={}
    for i in sys.argv[2:]:
        l = i.split('=', 1)
        if len(l) == 2:
            kwargs[l[0]] = l[1]
        else:
            args.append(i)
    function(*args, **kwargs)

