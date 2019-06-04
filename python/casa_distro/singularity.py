from __future__ import print_function

import os
import os.path as osp
import subprocess
import json
import tempfile
import shutil
import fnmatch
from subprocess import check_call, check_output
import glob
import sys

from casa_distro import log, six
from casa_distro.hash import file_hash, check_hash
from casa_distro.defaults import default_download_url
from . import downloader


def image_name_match(image_name, filters):
    '''
    Tests if an image name matches one of the filters.
    It uses fnmatch syntax.
    '''     
    for f in filters:
        if fnmatch.fnmatch(image_name, f):
            return True

def create_singularity_images(bwf_dir, image_name_filters=['cati/*'],
                              verbose=None):
    '''
    Creates singularity images by converting to docker images.
    Return the number of images processed.
    '''
    verbose = log.getLogFile(verbose)
    output = check_output(['docker', 'images', '--no-trunc'])
    images_tags = [i.split(None, 3)[:3] for i in output.split('\n')[1:] if i.strip()]

    images = dict([('%s:%s' %(i,t), iid) for i, t, iid in images_tags
                   if i != '<none>' and t not in ('<none>', 'latest')])
    images = dict([(i, iid) for i, iid in images.items()
                   if image_name_match(i, image_name_filters)])
    for docker_image, iid in images.items():
        singularity_image = osp.join(
            bwf_dir,
            docker_image.replace('/', '_').replace(':','_') + '.simg')
        docker_id_file = singularity_image + '.dockerid'
        if os.path.exists(docker_id_file):
            try:
                did = open(docker_id_file).read().strip()
                if did == iid:
                    print('image', singularity_image, 'is up-to-date.')
                    continue
            except:
                print('could not read latest docker ID for image',
                      singularity_image, ': recreating it.')
        print('Creating image', singularity_image, 'from', docker_image,
              file=verbose)
        if osp.exists(singularity_image):
            os.remove(singularity_image)
        stdout = subprocess.check_output(['docker', 'inspect', docker_image])
        image_info = json.loads(stdout)
        docker_img_config = image_info[0]['Config']
        env = dict(i.split('=', 1) for i in docker_img_config.get('Env',[]))
        env_path = {}
        for v in env.keys():
            if v.endswith('PATH'):
                env_path[v] = env.pop(v)
            
        entry_point = docker_img_config.get('Entrypoint')
        cmd = docker_img_config.get('Cmd')
        if entry_point:
            runscript = [[e] for e in entry_point]
            if cmd:
                runscript += [cmd]
        elif cmd:
            runscript = [cmd]
        tmp = tempfile.mkdtemp()
        try:
            container = subprocess.check_output(['docker', 'create', docker_image]).strip()
            try:
                docker_files = osp.join(tmp, 'docker')
                if not osp.exists(docker_files):
                    os.mkdir(docker_files)
                docker = subprocess.Popen(['docker', 'export', container], stdout=subprocess.PIPE)
                tar = subprocess.Popen(['sudo', 'tar', 'x'], stdin=docker.stdout, cwd=docker_files)
                tar.wait()
                try:
                    recipe = osp.join(tmp, 'singularity_recipe')
                    out = open(recipe, 'w')
                    print('''Bootstrap: localimage
From: %s

%%help
    Singularity image created from Docker image %s

%%environment
%s
%s
%s
%s

%%runscript
%s''' % (docker_files,
             docker_image,
        '\n'.join('    if [ -z "${%(var)s}" ];then export %(var)s=%(val)s;fi' \
                  % {'var': n, 'val': v} for n, v in six.iteritems(env)),
        '\n'.join('    if [ -z "${%(var)s_INIT}" ];'\
                  'then export %(var)s=%(val)s;' \
                  'else export %(var)s="${%(var)s_INIT}";fi' \
                  % {'var': n, 'val': v} for n, v in six.iteritems(env_path)),
        '\n'.join('    if [ -n "${%(var)s_PREPEND}" ];'\
                  'then export %(var)s="${%(var)s_PREPEND}:${%(var)s}";fi' \
                  % {'var': n} for n in env_path.keys()),
        '\n'.join('    if [ -n "${%(var)s_APPEND}" ];'\
                  'then export %(var)s="${%(var)s}:${%(var)s_APPEND}";fi' \
                  % {'var': n} for n in env_path.keys()),
        '\n'.join('. ' + ' '.join(["'%s'" % i for i in r]) for r in runscript)),        
                    file=out)
                    out.close()
                    subprocess.check_call(['sudo', '-E', 'singularity',
                                           'build', singularity_image, recipe])
                    image_hash = file_hash(singularity_image)
                    open(singularity_image + '.md5', 'w').write(image_hash)
                    open(docker_id_file, 'w').write(iid)
                finally:
                    subprocess.call(['sudo', 'rm', '-Rf', docker_files]) 
            finally:
                subprocess.call(['docker', 'rm', container])
        finally:
            shutil.rmtree(tmp)
        do = tempfile.NamedTemporaryFile(suffix='.tar')
    return len(images)


def get_image_filename(container_image, build_workflows_repository=None):
    if os.path.exists(container_image):
        return container_image
    image_file = container_image.replace('/', '_').replace(':', '_')
    if not osp.isabs(image_file):
        image_file = osp.join(build_workflows_repository, image_file)
    if not osp.exists(image_file) and not image_file.endswith('.simg'):
        image_file += '.simg'
    return image_file


def download_singularity_image(build_workflows_repository, container_image):
    image_path = get_image_filename(container_image,
                                    build_workflows_repository)
    image_file = osp.basename(image_path)
    url = '%s/%s' % (default_download_url, image_file)
    print('Downloading', image_path, 'from', url)
    tmp_path = image_path + '.tmp'
    try:
        downloader.download_file(url, tmp_path,
                                 callback=downloader.stdout_progress)
    except Exception as e:
        print('Unable to update singularity image from', 
              url, 'to', image_path)
        print(e)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return False
    
    tmp_md5 =  image_path + '.md5.tmp'
    try:
        downloader.download_file(url + '.md5', tmp_md5)
    except Exception as e:
        print('Unable to update singularity image hash from', 
              url + '.md5', 'to', image_path + '.md5')
        print(e)
        if os.path.exists(tmp_md5):
            os.unlink(tmp_md5)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return False
    if not check_hash(tmp_path, tmp_md5):
        os.unlink(tmp_md5)
        os.unlink(tmp_path)
        raise ValueError('Mismatching md5 hash on file %s' % image_path)
    if os.path.exists(image_path + '.dockerid'):
        os.unlink(image_path + '.dockerid')
    if os.path.exists(image_path):
        os.unlink(image_path)
    if os.path.exists(image_path + '.md5'):
        os.unlink(image_path + '.md5')
    shutil.move(tmp_path, image_path)
    shutil.move(tmp_md5, image_path + '.md5')
    try:
        downloader.download_file(url + '.dockerid', image_path + '.dockerid')
    except:
        pass # no docker id. oh, well...


def update_singularity_image(build_workflows_repository, container_image,
                             verbose=False):
    verbose = log.getLogFile(verbose)
    if os.path.exists(container_image):
        # If the image is actually a local filename, then we don't try to
        # update.
        return True
    image_path = get_image_filename(container_image,
                                    build_workflows_repository)
    image_file = osp.basename(image_path)
    if osp.exists(image_path):
        hash_file = image_file + '.md5'
        hash_path = image_path + '.md5'
        if osp.exists(hash_path):
            local_hash = open(hash_path).read()
            tmp = tempfile.NamedTemporaryFile()
            url = '%s/%s' % (default_download_url, hash_file)
            try:
                downloader.download_file(url, tmp.name)
            except Exception as e:
                print('Unable to update singularity image from', 
                      url, 'to', tmp.name)
                print(e)

            remote_hash = open(tmp.name).read()
            if remote_hash == local_hash:
                if verbose:
                    print('Not updating', image_path, 'which is identical to',
                          url, file=verbose)
                    
                return False
    download_singularity_image(build_workflows_repository, container_image)
    return True

    
def run_singularity(casa_distro, command, gui=False, interactive=False,
                    tmp_container=True, container_image=None,
                    cwd=None, env=None, container_options=[],
                    verbose=None):
    verbose = log.getLogFile(verbose)
    
    # With --cleanenv only variables prefixd by SINGULARITYENV_ are transmitted 
    # to the container
    singularity = ['singularity', 'run', '--cleanenv']
    if cwd:
        singularity += ['--pwd', cwd]
    for source, dest in six.iteritems(casa_distro.get('container_volumes',{})):
        source = source % casa_distro
        source = osp.expandvars(source)
        dest = dest % casa_distro
        dest = osp.expandvars(dest)
        singularity += ['--bind', '%s:%s' % (source, dest)]
        
    container_env = os.environ.copy()
    tmp_env = dict(casa_distro.get('container_env', {}))
    if gui:
        tmp_env.update(casa_distro.get('container_gui_env', {}))
    if env is not None:
        tmp_env.update(env)
    
    # Creates environment with variables prefixed by SINGULARITYENV_
    # with --cleanenv only these variables are given to the container
    for name, value in six.iteritems(tmp_env):
        value = value % casa_distro
        value = osp.expandvars(value)
        container_env['SINGULARITYENV_' + name] = value
    conf_options = casa_distro.get('container_options', [])
    if cwd:
        for i, opt in enumerate(conf_options):
            if opt == '--pwd':
                conf_options = conf_options[:i] + conf_options[i+2:]
                break
    options = list(conf_options)
    options += container_options
    if gui:
        gui_options = casa_distro.get('container_gui_options', [])
        if gui_options:
            options += [osp.expandvars(i) for i in gui_options
                        if i != '--no-nv']
        # handle --nv option, if a nvidia device is found
        if '--nv' not in options and os.path.exists('/dev/nvidiactl') \
                and '--no-nv' not in options:
            options.append('--nv')
        # remove --no-nv which is not a singularity option
        if '--no-nv' in options:
            options.remove('--no-nv')
    singularity += options
    if container_image is None:
        container_image = casa_distro.get('container_image')
        if container_image is None:
            raise ValueError('container_image is missing from casa_distro.json')
        container_image = get_image_filename(
            container_image,
            osp.dirname(osp.dirname(casa_distro['build_workflow_dir'])))
        if not osp.exists(container_image):
            raise ValueError("'%s' does not exist" % container_image)
    singularity += [container_image]
    singularity += command
    if verbose:
        print('-' * 40, file=verbose)
        print('Running singularity with the following command:', file=verbose)
        print(*("'%s'" % i for i in singularity), file=verbose)
        print('\nUsing the following environment:', file=verbose)
        for n in sorted(container_env):
            v = container_env[n]
            print('    %s=%s' % (n, v), file=verbose)
        print('-' * 40, file=verbose)
    check_call(singularity, env=container_env)



def create_writable_singularity_image(image, 
                                      build_workflow_directory,
                                      build_workflows_repository,            
                                      verbose):
    verbose = log.getLogFile(verbose)
    if build_workflow_directory:
        casa_distro_json = osp.join(build_workflow_directory, 'conf', 'casa_distro.json')
        casa_distro = json.load(open(casa_distro_json))
        image = casa_distro.get('container_image')
        
    read_image = get_image_filename(image, build_workflows_repository)
    write_image = read_image[:-4] + 'writable'
    check_call(['sudo', 'singularity', 'build', '--sandbox', write_image, read_image])


def singularity_root_shell(image, 
                           build_workflow_directory,
                           build_workflows_repository,            
                           verbose):
    verbose = log.getLogFile(verbose)
    if build_workflow_directory:
        casa_distro_json = osp.join(build_workflow_directory, 'conf', 'casa_distro.json')
        casa_distro = json.load(open(casa_distro_json))
        image = casa_distro.get('container_image')
        
    write_image = get_image_filename(image, build_workflows_repository)
    if not write_image.endswith('.writable.simg') \
            and not write_image.endswith('.writable'):
        if write_image.endswith('.simg'):
            write_image = write_image[:-5]
        write_image = write_image + '.writable'
    check_call(['sudo', 'singularity', 'shell', '--writable', write_image])

def clean_singularity_images(build_workflows_repository, image_names,
                             images_to_keep, verbose, interactive=True):
    verbose = log.getLogFile(verbose)
    image_name_filters = [i.replace('/', '_').replace(':', '_') for i in image_names.split(',')]
    image_files = []
    for filter in image_name_filters:
        image_files += glob.glob(osp.join(build_workflows_repository,
                                          filter + '.simg')) \
                       + glob.glob(osp.join(build_workflows_repository,
                                            filter + '.writable'))
    images_to_keep = set([get_image_filename(image, build_workflows_repository)
                          for image in images_to_keep.get('singularity', [])])
    remove_images = []
    for image_name in image_files:
        if image_name in images_to_keep:
            if verbose:
                print(image_name, 'is still in use', file=verbose)
                continue
        if interactive or verbose:
            print('to remove:', image_name, file=verbose)
        remove_images.append(image_name)
    confirm = ''
    if interactive and len(remove_images) != 0:
        print('proceed or confirm individually (i) ? (y/[n]/i): ', end='')
        sys.stdout.flush()
        confirm = sys.stdin.readline().strip().lower()
        if confirm not in ('y', 'yes', 'i', 'ind'):
            print('abort.')
            return

    for image_name in image_files:
        if image_name not in images_to_keep:
            if confirm in ('i', 'ind'):
                print('remove', image_name, '? (y/[n]): ', end='')
                c = sys.stdin.readline().strip().lower()
            else:
                c = 'y'
            if c in ('y', 'yes'):
                if verbose:
                    print('removing:', image_name, file=verbose)
                if os.path.isdir(image_name):
                    # writable image directory, needs root access
                    check_call(['sudo', 'rm', '-rf', image_name])
                else:
                    os.unlink(image_name)


