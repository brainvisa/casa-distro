# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import collections
from fnmatch import fnmatch
import sys
import os
import os.path as osp
import glob
import shutil
import json
import copy

from casa_distro.defaults import default_system
from casa_distro import six
from casa_distro import share_directories
from casa_distro.log import verbose_file
from casa_distro.docker import run_docker, update_docker_image


def update_dict_recursively(dict_to_update, dict_to_read):
    '''
    Recursively merge dict_to_read into dict_to_update
    '''
    for k, v in six.iteritems(dict_to_read):
        if (k in dict_to_update and isinstance(dict_to_update[k], dict)
                and isinstance(v, collections.Mapping)):
            update_dict_recursively(dict_to_update[k],
                                    dict_to_read[k])
        else:
            dict_to_update[k] = dict_to_read[k]


def iter_environments(build_workflows_repository,
                      type='*',
                      distro='*',
                      branch='*',
                      system='*'):
    for i in sorted(glob.glob(osp.join(build_workflows_repository, distro,
                                       '%s_%s' % (branch, system), 'host', 'conf'))):
        env_json = osp.join(i, 'casa_distro.json')
        if os.path.exists(env_json):
            env_conf = json.load(open(env_json))
            the_type = env_conf.get('type', 'dev')
            if fnmatch(the_type, type):
                env_conf['build_workflow_directory'] = osp.dirname(
                    osp.dirname(osp.dirname(env_json)))
                env_conf['type'] = the_type
                yield env_conf


def find_in_path(file):
    '''
    Look for a file in a series of directories contained in ``PATH`` environment variable.
    '''
    path = os.environ.get('PATH').split(os.pathsep)
    for i in path:
        p = osp.normpath(osp.abspath(i))
        if p:
            r = glob.glob(osp.join(p, file))
            if r:
                return r[0]

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
        except shutil.Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if shutil.WindowsError is not None and isinstance(why, shutil.WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)


def cp(src, dst, not_override=[], verbose=None):

    def override_exclusion(cur_src, names,
                           cur_dst, dst_names):
        excluded = []
        for n in not_override:
            if n in names:
                i = names.index(n)
                d = os.path.join(cur_dst, dst_names[i])
                if os.path.exists(d) or os.path.islink(d):
                    excluded.append(n)
                    if verbose:
                        print('file', d, 'exists,', 'skipping override.',
                              file=verbose)

        return excluded

    copytree(src, dst, ignore=override_exclusion)


def check_svn_secret(bwf_dir, warn_type='NOTE'):
    ''' Checks the svn.secret file does not exist. Print a message if it does
    not.

    Parameters:
    -----------
    bwf_dir: str
        build workflow directory
    warn_type: str
        warning message type ('NOTE', 'ERROR', ...)

    Returns:
    --------
        True if the file is here, False if it is missing
    '''
    if not os.path.exists(osp.join(bwf_dir, 'host', 'conf', 'svn.secret')):
        print('\n------------------------------------------------------------')
        print('**%s:**' % warn_type)
        print('Before using "casa_distro bv_maker" you will have to '
              'create the svn.secret file with your Bioproj login / password '
              'in order to access the BrainVisa repository.')
        print('Place it at the following location:\n')
        print(osp.join(bwf_dir, 'host', 'conf', 'svn.secret'))
        print('\nThis file is a shell script that must set the variables '
              'SVN_USERNAME and SVN_PASSWORD. Do not forget to properly quote '
              'the values if they contains special characters.')
        print('For instance, the file could contain the two following lines (replacing '
              '"your_login" and "your_password" by appropriate values:\n')
        print("SVN_USERNAME='your_login'")
        print("SVN_PASSWORD='your_password'\n")
        print('If you are only using open-source projects, you can use the '
              '"public" login/password: brainvisa / Soma2009\n')
        print('Remember also that you can edit and customize the projects to '
              'be built, by editing the following file:\n')
        print(osp.join(bwf_dir, 'host', 'conf', 'bv_maker.cfg'))
        print('------------------------------------------------------------')
        print()
        return False
    return True


def update_build_workflow(build_workflow_directory, verbose=None,
                          command=None):
    '''
    Update an existing build workflow directory. It basically:
    * recreates the casa_distro run script
    * writes a .bashrc in the casa home dir if there is not any yet.
    * runs the command 'git lfs install' if git-lfs is available

    Parameters
    ----------
    build_workflow_directory:
        Directory containing all files of a build workflow.
    verbose: bool
        verbose mode
    command: str
        casa_distro command actually called in the run script. May be either
        "host" (the calling command from the host system), "workflow" (use the
        sources from the build-workflow, the default), or a hard-coded path to
        the casa_distro command.
    '''
    bin_dir = os.path.join(build_workflow_directory, 'bin')
    if verbose:
        print('update_build_workflow:', build_workflow_directory)
    if not os.path.exists(bin_dir):
        if verbose:
            print('create directory:', bin_dir)
        os.mkdir(bin_dir)
    script_file = os.path.join(bin_dir, 'casa_distro')
    if command in (None, 'workflow'):
        # try to use casa_distro in sources from the build workflow, then if
        # it is not found, fallback to the calling one.
        branches = ['master', 'integration', 'release_candidate',
                    'latest_release']
        try_paths = [os.path.join(build_workflow_directory, 'src',
                                  'development', 'casa-distro', branch, 'bin',
                                  'casa_distro')
                     for branch in branches]
    elif command == 'host':
        # no default path, use the fallback
        try_paths = []
    else:
        try_paths = [command]
    try_paths = [p for p in try_paths if os.path.exists(p)]
    casa_distro_path = (try_paths
                        + [os.path.normpath(os.path.abspath(sys.argv[0]))])[0]
    if sys.platform.startswith('win'):
        # windows: .bat script
        script_file += '.bat'
        with open(script_file, 'w') as f:
            f.write('''@setlocal
@"%s" "%s" \\%*
@endlocal''' % (sys.executable, casa_distro_path))
    else:
        # unix: bash script
        with open(script_file, 'w') as f:
            f.write('''#!/bin/bash
exec %s %s "$@"''' % (sys.executable, casa_distro_path))
    os.chmod(script_file, 0o775)
    if verbose:
        print('created run script:', script_file)

    prepare_home(build_workflow_directory,
                 os.path.join(build_workflow_directory, 'host', 'home'),
                 verbose=verbose)


def prepare_home(build_workflow_directory, home_path, verbose=None):
    '''
    Prepare the home directory of the container.
    * writes a .bashrc in the casa home dir if there is not any yet.
    * runs the command 'git lfs install' if git-lfs is available


    Parameters
    ----------
    build_workflow_directory:
        Directory containing all files of a build workflow.
    verbose: bool
        verbose mode
    '''
    bashrc = os.path.join(home_path, '.bashrc')
    if not os.path.exists(bashrc):
        open(bashrc, 'w').write(r'''
if [ -f /etc/profile ]; then
    . /etc/profile
fi

# source any bash_completion scripts
if [ -d "$CASA_BUILD/etc/bash_completion.d" ]; then
    for d in "$CASA_BUILD/etc/bash_completion.d/"*; do
        if [ -f "$d" ]; then
            . "$d"
        fi
    done
fi

# colored prompt to show we are in a casa-distro shell
export PS1='\[\033[33m\]\u@\h \$\[\033[0m\] '
# convenient aliases
alias ls='ls -F --color'
alias ll='ls -als'
''')
    # initialize git-lfs for the local home
    # run_container(
    #     build_workflow_directory,
    #     ['bash', '-c',
    #      'type git-lfs > /dev/null 2>&1 && git lfs install || echo "not using git-lfs"'],
    #     verbose=verbose)


def merge_dict(d, od):
    ''' Deep-merge JSON objects (dictionaries are merged recursively, lists are
        concatenated)
    '''
    for key, v in od.items():
        if key not in d:
            d[key] = v
        else:
            oldv = d[key]
            if isinstance(oldv, dict):
                merge_dict(oldv, v)
            elif isinstance(oldv, list):
                oldv += v
            else:
                d[key] = v


def merge_config(casa_distro, conf):
    ''' Merge casa_distro dictionary config with an alternative config
        sub-directory found as key ``conf``
    '''
    if conf not in ('dev', '', None, 'default'):
        # an alternative conf has been specified: merge sub-dictionary
        casa_distro = copy.deepcopy(casa_distro)
        merge_dict(casa_distro, casa_distro.get('alt_configs', {})[conf])
    return casa_distro


# def update_container_image(build_workflows_repository, container_type,
#                            container_image, verbose=False):
#     if container_type == 'singularity':
#         update_singularity_image(build_workflows_repository,
#                                  container_image,
#                                  verbose=verbose)
#     elif container_type == 'docker':
#         update_docker_image(container_image)
#     else:
#         raise ValueError('%s is no a valid container system' %
#         container_type)


def delete_build_workflow(bwf_directory):
    shutil.rmtree(bwf_directory)
