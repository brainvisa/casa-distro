# coding: utf-8 

from __future__ import absolute_import
from __future__ import print_function

import errno
import json
import os
import os.path as osp
import shutil
from subprocess import check_call, check_output
import sys
import tempfile
import stat
import re

import casa_distro
from casa_distro import share_directory, linux_os_ids

# We need to duplicate this function to allow copying over
# an existing directory
def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().

    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    if os.path.isdir(src):
        names = os.listdir(src)
        dstnames = names
    else:
        names = [os.path.basename(src)]
        src = os.path.dirname(src)
        
        if os.path.isdir(dst):
            dstnames = names
        else:
            dstnames = [os.path.basename(dst)]
            dst = os.path.dirname(dst)
        
    if ignore is not None:
        ignored_names = ignore(src, names, 
                               dst, dstnames)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)
        
    errors = []
    for name, new_name in zip(names, dstnames):
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, new_name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                shutil.copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error, err:
            errors.extend(err.args[0])
        except EnvironmentError, why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError, why:
        if shutil.WindowsError is not None and isinstance(why, shutil.WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise shutil.Error, errors
    
def cp(src, dst, not_override=[], verbose=None):
    
    def override_exclusion(cur_src, names, 
                           cur_dst, dst_names):
        excluded = []
        for n in not_override:
            if n in names:
              i = names.index(n)
              d = os.path.join(cur_dst, dst_names[i])
              if os.path.exists(d):
                excluded.append(n)
                if verbose:
                    print('file', d, 'exists,', 'skipping override.', 
                          file=verbose)
        
        return excluded
    
    copytree(src, dst, ignore=override_exclusion)

dockerfile_template = '''FROM cati/casa-dev:%(system)s
# set rsa key of guest (localhost) in user ssh config at login time
RUN sed -i 's|#!/bin/sh|#!/bin/sh\\nssh-keyscan localhost >> $HOME/.ssh/known_hosts|' /usr/local/bin/entrypoint

%(non_root_commands)s

RUN mkdir %(home)s/.brainvisa && \
    ln -s $CASA_CONF/bv_maker.cfg %(home)s/.brainvisa/bv_maker.cfg

RUN mkdir -p $CASA_SRC/development/brainvisa-cmake
RUN mkdir -p $CASA_CUSTOM_BUILD
RUN /usr/local/bin/svn export https://bioproj.extra.cea.fr/neurosvn/brainvisa/development/brainvisa-cmake/branches/bug_fix $CASA_SRC/development/brainvisa-cmake/bug_fix
RUN mkdir /tmp/brainvisa-cmake
WORKDIR /tmp/brainvisa-cmake
RUN cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/bug_fix
RUN make install && cd .. && rm -r /tmp/brainvisa-cmake
WORKDIR /casa

# Create bashrc and/or update wine registry to add built 
# executables in path
RUN if [ -z "${WINEPREFIX}" ]; then \
echo 'if [ -f "$CASA_BUILD/bin/bv_env.sh" ]; then . "$CASA_BUILD/bin/bv_env.sh" "$CASA_BUILD"; fi' >> %(home)s/.bashrc; \
else \
__wine_casa_build="$(winepath -w ${CASA_BUILD})"; \
wineserver -k -w; \
/casa/brainvisa-cmake/bin/bv_wine_regedit \
        --registry-action 'prepend' \
        --value-path "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Environment\\PATH" \
        --value "${__wine_casa_build}\\bin"; \
/casa/brainvisa-cmake/bin/bv_wine_regedit \
        --registry-action 'prepend' \
        --value-path "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Environment\\PYTHONPATH" \
        --value "${__wine_casa_build}\\python"; \
/casa/brainvisa-cmake/bin/bv_wine_regedit \
        --registry-action 'set' \
        --value-path "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Environment\\QT_API" \
        --value "pyqt"; \
/casa/brainvisa-cmake/bin/bv_wine_regedit \
        --registry-action 'set' \
        --value-path "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Environment\\BRAINVISA_HOME" \
        --value "${__wine_casa_build}"; \
/casa/brainvisa-cmake/bin/bv_wine_regedit \
        --registry-action 'set' \
        --value-path "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Environment\\BRAINVISA_SHARE" \
        --value "${__wine_casa_build}\\share"; \
echo 'export PATH="$PATH:$CASA_BUILD/bin"' >> %(home)s/.bashrc; \
fi

ENV PATH=$PATH:$CASA_BUILD/bin:/casa/brainvisa-cmake/bin
ENV LD_LIBRARY_PATH=$CASA_BUILD/lib:/casa/brainvisa-cmake/lib
ENV PYHONPATH=$CASA_BUILD/python:/casa/brainvisa-cmake/python
RUN mkdir %(home)s/.ssh
'''

# For testing purpose, it may be necessary to run casa_distro as root in a Docker container.
# In that case only, the folowing commands are not included in the Dockerfile.
dockerfile_nonroot_commands = '''RUN addgroup --gid %(gid)s %(group)s
RUN adduser --disabled-login --home /home/user --uid %(uid)s --gid %(gid)s %(user)s
RUN chown %(user)s:%(group)s /casa
RUN if [ -d "${WINEPREFIX}" ]; then chown -R %(user)s:%(group)s "${WINEPREFIX}"; fi
USER %(user)s
'''


docker_run_template = '''#!/bin/bash
if [ -f %(build_workflow_dir)s/conf/docker_options ]; then
    . %(build_workflow_dir)s/conf/docker_options
fi

docker_cmd=
docker_arg=0
docker_rm=1
script_arg=1

while [[ $# -gt 0 ]]
do
    key="$1"

    if [ "$docker_arg" == 1 ]; then

        if [ "$1" == "--" ]; then
            # end of docker options
            docker_arg=0
            script_arg=0
        else
            DOCKER_OPTIONS="$DOCKER_OPTIONS $1"
        fi

    else

        if [ "$script_arg" == 0 ]; then

            docker_cmd="$docker_cmd $1"

        else

            case $key in
                -h|--help)
                echo "$0 [options] command [args]"
                echo "run command (with args) in docker using %(image_name)s image, casa-distro mount points, and host user. The script %(build_workflow_dir)s/conf/docker_options will be sourced to get additional docker options in the variable DOCKER_OPTIONS."
                echo "options:"
                echo "-X11         source an additional options script %(build_workflow_dir)s/conf/docker_options_x11"
                echo "             which will complete DOCKER_OPTIONS with X config."
                echo "-d|--docker  pass additional options to Docker. Following options will"
                echo "             be appended to DOCKER_OPTIONS. To end up docker options and"
                echo "             specify the command and its ards, the option delimier \"--\""
                echo "             should be used. Ex:"
                echo "             $0 -d -v /data_dir:/docker_data_dir -- ls /docker_data_dir"
                echo "-n|--no-rm   disable docker rm of container run"
                exit 1
                ;;

                -X11)
                if [ -f %(build_workflow_dir)s/conf/docker_options_x11 ]; then
                    . %(build_workflow_dir)s/conf/docker_options_x11
                fi
                ;;
                -d|--docker)
                docker_arg=1
                ;;
                -n|--no-rm)
                docker_rm=0
                ;;
                --)
                docker_arg=0
                script_arg=0
                ;;
                *)
                # Once started to parse the command to run, it is necessary
                # to disable parsing of docker options and script options
                # otherwise it is not possible to use defined script options (-d, -h, -n, -X11, ...)
                docker_arg=0
                script_arg=0
                docker_cmd="$docker_cmd $1"
                ;;
            esac
        fi
    fi
    shift # past argument or value
done

cmd="docker run"

if [ "${docker_rm}" == "1" ]; then
    cmd="${cmd} --rm"
fi

cmd="${cmd} -v %(build_workflow_dir)s/conf:/casa/conf \
            -v %(build_workflow_dir)s/src:/casa/src \
            -v %(build_workflow_dir)s/build:/casa/build \
            -v %(build_workflow_dir)s/install:/casa/install \
            -v %(build_workflow_dir)s/pack:/casa/pack \
            -v %(build_workflow_dir)s/tests:/casa/tests \
            -v %(build_workflow_dir)s/custom/src:/casa/custom/src \
            -v %(build_workflow_dir)s/custom/build:/casa/custom/build \
            -v $HOME/.ssh/id_rsa:%(home)s/.ssh/id_rsa \
            -v $HOME/.ssh/id_rsa.pub:%(home)s/.ssh/id_rsa.pub \
            -e CASA_BRANCH=%(casa_branch)s \
            -e CASA_HOST_DIR=%(build_workflow_dir)s \
            --net=host ${DOCKER_OPTIONS} \
            %(image_name)s \
            $docker_cmd"
echo "$cmd"
exec $cmd
'''

docker_test_run_template = '''#!/bin/bash
if [ -f %(build_workflow_dir)s/conf/docker_options ]; then
    . %(build_workflow_dir)s/conf/docker_options
fi

docker_cmd=
docker_arg=0
script_arg=1
image_arg=0
if [ -n "${IMAGE_NAME}" ]; 
then
    image_name="${IMAGE_NAME}"
else
    image_name="cati/casa-test:%(system)s"
fi

while [[ $# -gt 0 ]]
do
    key="$1"

    if [ "$docker_arg" == 1 ]; then

        if [ "$1" == "--" ]; then
            # end of docker options
            docker_arg=0
            script_arg=0
        else
            DOCKER_OPTIONS="$DOCKER_OPTIONS $1"
        fi

    else
        if [ "$image_arg" == 1 ]; then
            image_name="$1"
            image_arg=0
        else

            if [ "$script_arg" == 0 ] && [ "$image_arg" == 0 ]; then

                docker_cmd="$docker_cmd $1"

            else

                case $key in
                    -h|--help)
                    echo "$0 [options] command [args]"
                    echo "run command (with args) in docker using ${image_name} image, casa-distro mount points, and host user. The script %(build_workflow_dir)s/conf/docker_options will be sourced to get additional docker options in the variable DOCKER_OPTIONS."
                    echo "options:"
                    echo "-X11         source an additional options script %(build_workflow_dir)s/conf/docker_options_x11"
                    echo "             which will complete DOCKER_OPTIONS with X config."
                    echo "-d|--docker  pass additional options to Docker. Following options will"
                    echo "             be appended to DOCKER_OPTIONS. To end up docker options and"
                    echo "             specify the command and its ards, the option delimier \"--\""
                    echo "             should be used. Ex:"
                    echo "             $0 -d -v /data_dir:/docker_data_dir -- ls /docker_data_dir"
                    exit 1
                    ;;

                    -X11)
                    if [ -f %(build_workflow_dir)s/conf/docker_options_x11 ]; then
                        . %(build_workflow_dir)s/conf/docker_options_x11
                    fi
                    ;;
                    -d|--docker)
                    docker_arg=1
                    ;;
                    --)
                    docker_arg=0
                    script_arg=0
                    ;;
                    -i|--image)
                    docker_arg=0
                    script_arg=0
                    image_arg=1
                    ;;
                    *)
                    # Once started to parse the command to run, it is necessary
                    # to disable parsing of docker options and script options
                    # otherwise it is not possible to use defined script options (-d, -h, -n, -X11, ...)
                    docker_arg=0
                    script_arg=0
                    docker_cmd="$docker_cmd $1"
                    ;;
                esac
            fi
        fi

    fi
    shift # past argument or value
done


cmd="docker run --rm \
                -v %(build_workflow_dir)s/conf:/casa/conf \
                -v %(build_workflow_dir)s/src:/casa/src \
                -v %(build_workflow_dir)s/build:/casa/build \
                -v %(build_workflow_dir)s/install:/casa/install \
                -v %(build_workflow_dir)s/pack:/casa/pack \
                -v %(build_workflow_dir)s/tests:/casa/tests \
                -v %(build_workflow_dir)s/custom/src:/casa/custom/src \
                -v %(build_workflow_dir)s/custom/build:/casa/custom/build \
                -v $HOME/.ssh/id_rsa:%(home)s/.ssh/id_rsa \
                -v $HOME/.ssh/id_rsa.pub:%(home)s/.ssh/id_rsa.pub \
                %(non_root_options)s \
                -e HOME=/casa/tests \
                -e CASA_BRANCH=%(casa_branch)s \
                --net=bridge ${DOCKER_OPTIONS} \
                $image_name \
                $docker_cmd"
echo "$cmd"
exec $cmd
'''

docker_x11_options = '''# options to setup X11 in docker
# the script tries to select and setup nvidia drivers and libGL,
# unless the following USE_NVIDIA variable is unset or set empty.
USE_NVIDIA=1

DOCKER_OPTIONS="$DOCKER_OPTIONS -v /tmp/.X11-unix:/tmp/.X11-unix -e QT_X11_NO_MITSHM=1 --privileged -e DISPLAY=$DISPLAY -v /usr/share/X11/locale:/usr/share/X11/locale:ro"

if [ -n "$USE_NVIDIA" ] ; then
    if [ -c "/dev/nvidiactl" ]; then
        NV_DIR=$(\ls -d /usr/lib/nvidia-???)
        DOCKER_OPTIONS="$DOCKER_OPTIONS --device=/dev/nvidia0:/dev/nvidia0 --device=/dev/nvidiactl -v $NV_DIR:/usr/lib/nvidia-drv:ro -e LD_LIBRARY_PATH=/usr/lib/nvidia-drv"
    fi
fi
'''


def get_docker_version():
    dverout = check_output(['docker', '-v'])
    r = re.match('Docker version ([0-9.]+).*$', dverout)
    return [int(x) for x in r.group(1).split('.')]


def create_build_workflow_directory(build_workflow_directory, 
                                    distro='opensource',
                                    casa_branch='latest_release',
                                    system=linux_os_ids[0],
                                    not_override=[],
                                    verbose=None, base_distro=None):
    '''
    Initialize a new build workflow directory. This creates a conf subdirectory
    with bv_maker.cfg and svn.secret files that can be edited before
    compilation.

    Parameters
    ----------
    build_workflow_directory:
        Directory containing all files of a build workflow. The following
        subdirectories are expected:
            conf: configuration of the build workflow (BioProj passwords, bv_maker.cfg, etc.)
            src*: source of selected components for the workflow.
            build*: build directory used for compilation. 
            install*: directory where workflow components are installed.
            pack*: directory containing distribution packages
    distro:
        Name of a set of configuration files. Either a predefined value
        (opensource, brainvisa, cati), or a free value if base_distro is
        specified.
    casa_branch:
        bv_maker branch to use (latest_release, bug_fix or trunk)
    system:
        Name of the target system.
    not_override:
        a list of file name that must not be overrided if they already exist
    base_distro:
        Name of a predefined set of configuration files, in the case distro is
        not one of the predefined known ones.

    * Typically created by bv_maker but may be extended in the future.

    '''
    # On Windows OS, we do not manage user and group for docker images
    is_win = sys.platform.startswith('win')
    
    if is_win:
        import getpass
    else:
        import grp
        import pwd
    
    bwf_dir = osp.normpath(osp.abspath(build_workflow_directory))
    print('build_workflow_directory:', build_workflow_directory)
    distro_dir = osp.join(share_directory, 'docker', distro)
    if not osp.exists(distro_dir):
        if base_distro is not None:
            distro_dir = osp.join(share_directory, 'docker', base_distro)
        else:
            raise ValueError('distro value %s is not a predefined value: '
                             'base_distro should be provided' % distro)
    if not osp.exists(distro_dir):
        if base_distro is None:
            base_distro = distro
        raise ValueError('distro %s is not found' % base_distro)
    os_dir = osp.join(distro_dir, system)
    all_subdirs = ('conf', 'src', 'build', 'install', 'tests', 'pack',
                   'custom', 'custom/src', 'custom/build')
    if not osp.exists(bwf_dir):
        os.mkdir(bwf_dir)
    for subdir in all_subdirs:
        sub_bwf_dir = osp.join(bwf_dir, subdir)
        if not osp.exists(sub_bwf_dir):
            os.mkdir(sub_bwf_dir)
        sub_distro_dir = osp.join(distro_dir, subdir)
        if osp.exists(sub_distro_dir):
            for i in os.listdir(sub_distro_dir):
                cp(osp.join(sub_distro_dir, i), osp.join(sub_bwf_dir, i), 
                   not_override=not_override, verbose=verbose)
        sub_os_dir = osp.join(os_dir, subdir)
        if osp.exists(sub_os_dir):
            for i in os.listdir(sub_os_dir):
                cp(osp.join(sub_os_dir, i), osp.join(sub_bwf_dir, i),
                   not_override=not_override, verbose=verbose)
    
    # Replacement of os.getlogin that fail sometimes
    if is_win:
        user = getpass.getuser()
    else:
        user = pwd.getpwuid(os.getuid()).pw_name

    local_image_name = 'casa-dev-%s:%s' % (system, user)
    template_params = {
        'user': user,
        #'container_name': 'casa_bwf_%s_%s_%s' % (distro, casa_branch, system),
        'system': system,
        'build_workflow_dir': bwf_dir,
        'image_name': local_image_name,
        'casa_branch': casa_branch,
        'home': ('/home/user' if not is_win and os.getuid() else '/root'), 
        'non_root_options': ''
    }
    
    if not is_win:
        template_params.update(
            {'group': grp.getgrgid(os.getgid()).gr_name,
             'uid': os.getuid(),
             'gid': os.getgid(),
             'non_root_options': '-u %s:%s -e USER=%s' \
                                 % (os.getuid(), os.getgid(), user)})

    if not os.path.isdir(osp.join(bwf_dir, 'docker')):
        os.mkdir(osp.join(bwf_dir, 'docker'))
    
    if not is_win and os.getuid():
        template_params['non_root_commands'] = dockerfile_nonroot_commands \
                                               % template_params
    else:
        template_params['non_root_commands'] = ''
    
    print(dockerfile_template % template_params,
          file=open(osp.join(bwf_dir, 'docker', 'Dockerfile'), 'w'))

    print('Creating personal docker image...')
    docker_ver = get_docker_version()
    # Docker 1.13 adds the --network option to build commands.
    # This is useful to avoid a DNS (/etc/resolv.conf) problem happening on
    # many Ubuntu computers where the host /etc/resolv.conf uses 127.0.0.1
    # Unfortunately it is not available in older releases of docker, including
    # those shipped in Ubuntu 16.04 (which is 1.12).
    # A possible fix if this doesn't work could be to use the host system
    # if svn is installed here, to retreive brainvisa-cmake, then use COPY
    # to install it in the docker image. But it would still not work in all
    # cases (when svn is not present on the host).
    if docker_ver >= [1, 13]:
        cmd = ['docker', 'build', '--network=host']
    else:
        cmd = ['docker', 'build']
    cmd += ['-t', local_image_name, osp.join(bwf_dir, 'docker')]
    print(*cmd)
    check_call(cmd)

    print(docker_run_template % template_params,
          file=open(osp.join(bwf_dir, 'run_docker.sh'), 'w'))
    os.chmod(osp.join(bwf_dir, 'run_docker.sh'),
             stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH | stat.S_IWRITE
             | stat.S_IEXEC | stat.S_IWGRP)
    print(docker_test_run_template % template_params,
          file=open(osp.join(bwf_dir, 'run_docker_test.sh'), 'w'))
    os.chmod(osp.join(bwf_dir, 'run_docker_test.sh'),
             stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH | stat.S_IWRITE
             | stat.S_IEXEC | stat.S_IWGRP)
    # create a default options file
    if not os.path.exists(osp.join(bwf_dir, 'conf', 'docker_options')):
        if 'windows' in system: # cross-compilation system
            # needs privileged to setup .exe binary execution using wine
            print('DOCKER_OPTIONS="$DOCKER_OPTIONS --privileged"\n',
                  file=open(osp.join(bwf_dir, 'conf', 'docker_options'), 'w'))
        else:
            print('DOCKER_OPTIONS="$DOCKER_OPTIONS"\n',
                  file=open(osp.join(bwf_dir, 'conf', 'docker_options'), 'w'))
    if not os.path.exists(osp.join(bwf_dir, 'conf', 'docker_options_x11')):
        print(docker_x11_options,
              file=open(osp.join(bwf_dir, 'conf', 'docker_options_x11'), 'w'))





        
def find_docker_image_files(base_directory):
    '''
    Return a sorted list of dictionary corresponding to the content of
    all the "casa_distro_docker.yaml" files located in given directory.
    The result is sorted according to the depencies declared in the files.
    '''
    import yaml
    
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

def create_docker_images(image_name_filters = ['*']):
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

                cmd = ['docker', 'build', '--force-rm',
                       '--tag', image_full_name, target_directory]
                print('-'*40)
                print('Creating image %s' % image_full_name)
                print(*cmd)
                print('Docker context:', os.listdir(target_directory))
                print('-'*40)
                check_call(cmd)
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

def publish_docker_images(image_name_filters = ['*']):
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
                image_full_name = 'cati/%s:%s' % (image_name, tag)
                if not image_name_match(image_full_name, image_name_filters):
                    continue
                
                check_call(['docker', 'push', image_full_name])


def create_build_workflow(bwf_repository, distro='opensource',
                          branch='latest_release', system=None, 
                          not_override=[],
                          verbose=None, base_distro=None):
    if system is None:
        system = casa_distro.linux_os_ids[0]
    bwf_directory = osp.join(bwf_repository, '%s' % distro, '%s_%s' % (branch, system))
    if not osp.exists(bwf_directory):
        os.makedirs(bwf_directory)
    create_build_workflow_directory(bwf_directory, distro, branch, system, 
                                    not_override, verbose=verbose,
                                    base_distro=base_distro)


def run_docker(bwf_repository, distro='opensource', branch='latest_release', 
               system=None, X=False, docker_rm=True, docker_options=[], 
               args_list=[]):
    '''Run any command in docker with the config of the given repository
    '''
    if system is None:
        system = casa_distro.linux_os_ids[0]
    bwf_directory = osp.join(bwf_repository, '%s' % distro,
                             '%s_%s' % (branch, system))
    run_docker = osp.join(bwf_directory, 'run_docker.sh')
    cmd = ['/bin/bash', run_docker]
    if not bool(docker_rm):
        cmd.append('-no-rm')
        
    if bool(X):
        cmd.append('-X11')
    if len(docker_options) > 0:
        cmd += ['-d'] + docker_options + ['--']

    cmd += args_list
    check_call(cmd)


def run_docker_shell(bwf_repository, distro='opensource',
                     branch='latest_release', system=None, X=False, 
                     docker_rm=True, args_list=[]):
    '''Run a bash shell in docker with the config of the given repository
    '''
    run_docker(bwf_repository, distro=distro, branch=branch, 
               system=system, X=X, docker_rm=docker_rm, docker_options=['-it'], 
               args_list=['/bin/bash'] + args_list)


def run_docker_bv_maker(bwf_repository, distro='opensource',
                        branch='latest_release', system=None, X=False, 
                        docker_rm=True, args_list=[]):
    '''Run bv_maker in docker with the config of the given repository
    '''
    run_docker(bwf_repository, distro=distro, branch=branch, 
               system=system, X=X, docker_rm=docker_rm, docker_options=[], 
               args_list=['bv_maker'] + args_list)

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

