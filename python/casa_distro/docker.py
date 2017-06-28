# coding: utf-8 

from __future__ import absolute_import
from __future__ import print_function

import errno
import grp
import json
import os
import os.path as osp
import pwd
import shutil
from subprocess import check_call
import sys
import tempfile
import yaml
import stat

import casa_distro
from casa_distro import share_directory, linux_os_ids


def cp(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as e:
        if e.errno != errno.ENOTDIR:
            raise
        shutil.copy2(src, dst)

#docker_compose_template = '''version: '2'

#services:
  #bwf:
    #image: %(image_name)s
    #build:
      #context: %(build_workflow_dir)s
    #container_name: %(container_name)s
    #volumes:
     #- %(build_workflow_dir)s/conf:/casa/conf
     #- %(build_workflow_dir)s/src:/casa/src
     #- %(build_workflow_dir)s/build:/casa/build
     #- %(build_workflow_dir)s/install:/casa/install
     #- %(build_workflow_dir)s/pack:/casa/pack
    #environment:
     #- CASA_BRANCH=%(casa_branch)s
#'''

dockerfile_template = '''FROM cati/casa-dev:%(system)s
RUN addgroup --gid %(gid)s %(group)s
RUN adduser --disabled-login --home /home/user --uid %(uid)s --gid %(gid)s %(user)s
RUN chown -R %(user)s:%(group)s /casa
USER %(user)s
RUN mkdir /home/user/.brainvisa && \
    ln -s $CASA_CONF/bv_maker.cfg /home/user/.brainvisa/bv_maker.cfg

RUN mkdir -p $CASA_SRC/development/brainvisa-cmake
RUN /usr/local/bin/svn export https://bioproj.extra.cea.fr/neurosvn/brainvisa/development/brainvisa-cmake/branches/bug_fix $CASA_SRC/development/brainvisa-cmake/bug_fix
RUN mkdir /tmp/brainvisa-cmake
WORKDIR /tmp/brainvisa-cmake
RUN cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/bug_fix
RUN make install

RUN echo 'if [ -f "$CASA_BUILD/bin/bv_env.sh" ]; then . "$CASA_BUILD/bin/bv_env.sh" "$CASA_BUILD"; fi' >> /home/user/.bashrc

ENV PATH=$PATH:$CASA_BUILD/bin:/casa/brainvisa-cmake/bin
ENV LD_LIBRARY_PATH=$CASA_BUILD/lib:/casa/brainvisa-cmake/lib
ENV PYHONPATH=$CASA_BUILD/python:/casa/brainvisa-cmake/python
'''

docker_run_template = '''#!/bin/bash
if [ -f %(build_workflow_dir)s/conf/docker_options ]; then
    . %(build_workflow_dir)s/conf/docker_options
fi
if [ "$1" == "-X11" ]; then
    shift
    if [ -f %(build_workflow_dir)s/conf/docker_options_x11 ]; then
        . %(build_workflow_dir)s/conf/docker_options_x11
    fi
fi
docker run --rm -it -v %(build_workflow_dir)s/conf:/casa/conf -v %(build_workflow_dir)s/src:/casa/src -v %(build_workflow_dir)s/build:/casa/build -v %(build_workflow_dir)s/install:/casa/install -e CASA_BRANCH=%(casa_branch)s --net=host ${DOCKER_OPTIONS} %(image_name)s "$@"
'''


#docker_command_template = [
    #'docker-compose',
    #'-f', '%(build_workflow_dir)s/docker-compose.yml',
    #'run',
    #'--rm',
    #'bwf',
    #'/bin/bash'
#]


def create_build_workflow_directory(build_workflow_directory, 
                                    distro='opensource',
                                    casa_branch='latest_release',
                                    system=linux_os_ids[0]):
    '''
    Initialize a new build workflow directory. This creates a conf subdirectory with
    bv_maker.cfg and svn.secret files that can be edited before compilation.
    
    build_workflow_directory: Directory containing all files of a build workflow. The following
        subdirectories are expected :
            conf: configuration of the build workflow (BioProj passwords, bv_maker.cfg, etc.)
            src*: source of selected components for the workflow.
            build*: build directory used for compilation. 
            install*: directory where workflow components are installed.
            pack*: directory containing distribution packages
    
    distro: Name of a predefined set of configuration files.

    casa_branch: bv_maker branch to use (latest_release, bug_fix or trunk)

    system: Name of the target system.
    
    * Typically created by bv_maker but may be extended in the future.

    '''
    bwf_dir = osp.normpath(osp.abspath(build_workflow_directory))
    print('build_workflow_directory:', build_workflow_directory)
    distro_dir = osp.join(share_directory, 'docker', distro)
    os_dir = osp.join(distro_dir, system)
    all_subdirs = ('conf', 'src', 'build', 'install', 'pack')
    if not osp.exists(bwf_dir):
        os.mkdir(bwf_dir)
    for subdir in all_subdirs:
        sub_bwf_dir = osp.join(bwf_dir, subdir)
        if not osp.exists(sub_bwf_dir):
            os.mkdir(sub_bwf_dir)
        sub_distro_dir = osp.join(distro_dir, subdir)
        if osp.exists(sub_distro_dir):
            for i in os.listdir(sub_distro_dir):
                cp(osp.join(sub_distro_dir, i), osp.join(sub_bwf_dir, i))
        sub_os_dir = osp.join(os_dir, subdir)
        if osp.exists(sub_os_dir):
            for i in os.listdir(sub_os_dir):
                cp(osp.join(sub_os_dir, i), osp.join(sub_bwf_dir, i))
    
    # Replacement of os.getlogin that fail sometimes
    user = pwd.getpwuid(os.getuid()).pw_name
    local_image_name = 'casa-dev-%s:%s' % (system, user)
    template_params = {
        'user': user,
        'uid': os.getuid(),
        'group': grp.getgrgid(os.getgid()).gr_name,
        'gid': os.getgid(),
        'container_name': 'casa_bwf_%s_%s_%s' % (distro, casa_branch, system),
        'system': system,
        'build_workflow_dir': bwf_dir,
        'image_name': local_image_name,
        'casa_branch': casa_branch,        
    }

    print(dockerfile_template % template_params, file=open(osp.join(bwf_dir, 'Dockerfile'), 'w'))

    # warning: docker-compose is recent and is not available in older
    # docker releases, which limits somewhat when we don't absolutely
    # need it.
    #print(docker_compose_template % template_params, file=open(osp.join(bwf_dir, 'docker-compose.yml'), 'w'))
    
    #cmd = [i % template_params for i in docker_command_template]
    #print(' '.join(cmd), file=open(osp.join(bwf_dir, 'build.sh'), 'w'))

    print('Creating personal docker image...')
    cmd = ['docker', 'build', '-t', local_image_name, bwf_dir]
    print(*cmd)
    check_call(cmd)

    print(docker_run_template % template_params,
          file=open(osp.join(bwf_dir, 'run_docker.sh'), 'w'))
    os.chmod(osp.join(bwf_dir, 'run_docker.sh'),
             stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH | stat.S_IWRITE
             | stat.S_IEXEC | stat.S_IWGRP)
    # create a default options file
    if not os.path.exists(osp.join(bwf_dir, 'conf', 'docker_options')):
        print('DOCKER_OPTIONS=\n',
              file=open(osp.join(bwf_dir, 'conf', 'docker_options'), 'w'))
    if not os.path.exists(osp.join(bwf_dir, 'conf', 'docker_options_x11')):
        print('DOCKER_OPTIONS="$DOCKER_OPTIONS '
              '-v /tmp/.X11-unix:/tmp/.X11-unix -e QT_X11_NO_MITSHM=1 '
              '--privileged -e DISPLAY=$DISPLAY"\n',
              file=open(osp.join(bwf_dir, 'conf', 'docker_options_x11'), 'w'))





        
def find_docker_image_files(base_directory):
    '''
    Return a sorted list of dictionary corresponding to the content of
    all the "casa_distro_docker.yaml" files located in given directory.
    The result is sorted according to the depencies declared in the files.
    '''
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


def create_docker_images():
    '''
    Creates all docker images that are declared in 
    find_docker_image_files(casa_distro_dir) where casa_distro_dir is the
    "docker" directory located in the directory casa_distro.share_directory.
    
    This function is still work in progress. Its paramaters and behaviour may
    change.
    '''
    
    error = False
    for images_dict in find_docker_image_files(osp.join(casa_distro.share_directory, 'docker')):
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
                    if f.endswith('.template'):
                        content = apply_template_parameters(open(osp.join(source_directory, f)).read(), template_parameters)
                        open(osp.join(target_directory, f[:-9]), 'w').write(content)
                    else:
                        content = open(osp.join(source_directory, f)).read()
                        open(osp.join(target_directory, f), 'w').write(content)
                image_full_name = 'cati/%s:%s' % (image_name, image_tags[-1])
                print('-'*40)
                print('Creating image %s' % image_full_name)
                print('-'*40)
                check_call(['docker', 'build', '--pull', '--force-rm', '--tag', image_full_name, target_directory])
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

def publish_docker_images():
    '''
    Publish, on DockerHub, all docker images that are declared in 
    find_docker_image_files(casa_distro_dir) where casa_distro_dir is the
    "docker" directory located in the directory casa_distro.share_directory.
    
    This function is still work in progress. Its paramaters and behaviour may
    change.
    '''
    import casa_distro
    
    for images_dict in find_docker_image_files(osp.join(casa_distro.share_directory, 'docker')):
        base_directory = tempfile.mkdtemp()
        source_directory, filename = osp.split(images_dict['filename'])
        for image_source in images_dict['image_sources']:
            template_parameters = { 'casa_version': casa_distro.info.__version__ }
            template_parameters.update(image_source.get('template_files_parameters', {}))
            
            image_name = apply_template_parameters(image_source['name'], template_parameters)
            image_tags = [apply_template_parameters(i, template_parameters) for i in image_source['tags']]
            for tag in image_tags:
                check_call(['docker', 'push', 'cati/%s:%s' % (image_name, tag)])


def create_build_workflow(bwf_repository, distro='opensource',
                          branch='latest_release', system=None):
    if system is None:
        system = casa_distro.linux_os_ids[0]
    bwf_directory = osp.join(bwf_repository, '%s' % distro, '%s_%s' % (branch, system))
    if not osp.exists(bwf_directory):
        os.makedirs(bwf_directory)
    create_build_workflow_directory(bwf_directory, distro, branch, system)


def run_docker(bwf_repository, distro='opensource',
               branch='latest_release', system=None, X=False, *args):
    '''Run any command in docker with the config of the given repository
    '''
    if system is None:
        system = casa_distro.linux_os_ids[0]
    bwf_directory = osp.join(bwf_repository, '%s' % distro,
                             '%s_%s' % (branch, system))
    run_docker = osp.join(bwf_directory, 'run_docker.sh')
    cmd = ['/bin/bash', run_docker]
    if bool(X):
        cmd.append('-X11')
    cmd += list(args)
    print('RUN DOCKER COMMAND:')
    print(*cmd)
    check_call(cmd)


def run_docker_shell(bwf_repository, distro='opensource',
                     branch='latest_release', system=None, X=False,
                     args_list=[]):
    '''Run a bash shell in docker with the config of the given repository
    '''
    run_docker(bwf_repository, distro, branch, system, X, '/bin/bash',
               *args_list)


def run_docker_bv_maker(bwf_repository, distro='opensource',
                        branch='latest_release', system=None, X=False,
                        args_list=[]):
    '''Run bv_maker in docker with the config of the given repository
    '''
    run_docker(bwf_repository, distro, branch, system, X, 'bv_maker',
               *args_list)



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
