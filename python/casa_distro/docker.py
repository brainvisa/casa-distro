# coding: utf-8 

import errno
import grp
import os
import os.path as osp
import pwd
import shutil
import subprocess

from casa_distro import share_directory, linux_os_ids


def cp(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as e:
        if e.errno != errno.ENOTDIR:
            raise
        shutil.copy2(src, dst)

dockerfile_template = '''FROM cati/casa-dev:ubuntu-12.04
ARG UID=%(uid)s
ARG GID=%(gid)s
ARG USER=%(user)s
ARG GROUP=%(group)s
ARG HOME=/home/user

RUN addgroup --gid $GID $GROUP
RUN adduser --disabled-login --home $HOME --uid $UID --gid $GID $USER
USER $USER
RUN mkdir $HOME/.brainvisa && \
    ln -s $CASA_CONF/bv_maker.cfg $HOME/.brainvisa/bv_maker.cfg

RUN /usr/local/bin/svn export https://bioproj.extra.cea.fr/neurosvn/brainvisa/development/brainvisa-cmake/branches/bug_fix $CASA_SRC/development/brainvisa-cmake/bug_fix
RUN mkdir /tmp/brainvisa-cmake
WORKDIR /tmp/brainvisa-cmake
RUN cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/bug_fix
RUN make install

ENV PATH=$PATH:$CASA_INSTALL/bin:/casa/brainvisa-cmake/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CASA_INSTALL/lib::/casa/brainvisa-cmake/lib
ENV PYHONPATH=$PYTHONPATH:$CASA_INSTALL/python::/casa/brainvisa-cmake/python
'''

docker_command_template = [
    'docker', 'run',
    '--name', '%(container_name)s',
    '-v', '"%(build_workflow_dir)s/conf:/casa/conf"',
    '-v', '"%(build_workflow_dir)s/src:/casa/src"',
    '-v', '"%(build_workflow_dir)s/build:/casa/build"',
    '-v', '"%(build_workflow_dir)s/install:/casa/install"',
    '-v', '"%(build_workflow_dir)s/pack:/casa/pack"',
    '-e', 'CASA_BRANCH="%(casa_branch)s"',
    '-it', '--rm',
    '%(image_name)s',
    '/bin/bash'
]

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
    distro_dir = osp.join(share_directory, 'docker', distro)
    os_dir = osp.join(distro_dir, system)
    all_subdirs = ('conf', 'src', 'build', 'install', 'pack')
    os.mkdir(bwf_dir)
    for subdir in all_subdirs:
        os.mkdir(osp.join(bwf_dir, subdir))
        sub_distro_dir = osp.join(distro_dir, subdir)
        if osp.exists(sub_distro_dir):
            for i in os.listdir(sub_distro_dir):
                cp(osp.join(sub_distro_dir, i), osp.join(bwf_dir, subdir, i))
        sub_os_dir = osp.join(os_dir, subdir)
        if osp.exists(sub_os_dir):
            for i in os.listdir(sub_os_dir):
                cp(osp.join(sub_os_dir, i), osp.join(bwf_dir, subdir, i))
    
    # Replacement of os.getlogin that fail sometimes
    user = pwd.getpwuid(os.getuid()).pw_name
    local_image_name = 'casa-dev-%s:%s' % (system, user)
    template_params = {
        'user': user,
        'uid': os.getuid(),
        'group': grp.getgrgid(os.getgid()).gr_name,
        'gid': os.getgid(),
        
    }
    print >> open(osp.join(bwf_dir, 'Dockerfile'), 'w'), dockerfile_template % template_params
    subprocess.check_call(['docker', 'build', '-t', local_image_name, bwf_dir])
    
    template_params = {
        'container_name': 'casa_bwf_%s_%s_%s' % (distro, casa_branch, system),
        'build_workflow_dir': bwf_dir,
        'image_name': local_image_name,
        'casa_branch': casa_branch,
    }
    cmd = [i % template_params for i in docker_command_template]
    print >> open(osp.join(bwf_dir, 'create_container.sh'), 'w'), ' '.join(cmd)

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
        