from __future__ import print_function

import os
import os.path as osp
import subprocess
import json
import tempfile
import shutil
import fnmatch
from subprocess import check_call, check_output

from casa_distro import log, six
from casa_distro.hash import file_hash
from casa_distro.defaults import default_download_url

try:
    # Try Python 3 only import
    from urllib.request import urlretrieve
except ImportError:
    # Provide a Python 2 implementation of urlretrieve
    import urllib2
    def urlretrieve(url, filename):
        buffer_size = 1024 * 4
        input = urllib2.urlopen(url)
        with open(filename,'wb') as output:
            while True:
                buffer = input.read(buffer_size)
                if buffer:
                    output.write(buffer)
                if len(buffer) < buffer_size:
                    break

def image_name_match(image_name, filters):
    '''
    Tests if an image name matches one of the filters.
    It uses fnmatch syntax.
    '''     
    for f in filters:
        if fnmatch.fnmatch(image_name, f):
            return True

def create_singularity_images(bwf_dir, image_name_filters = ['cati/*'],
                              verbose=None):
    '''
    Creates singularity images by converting to docker images.
    Return the number of images processed.
    '''
    verbose = log.getLogFile(verbose)
    output = check_output(['docker', 'images'])
    images_tags = [i.split(None, 2)[:2] for i in output.split('\n')[1:] if i.strip()]
    images = ['%s:%s' %(i,t) for i, t in images_tags if i != '<none>' and t not in ('<none>', 'latest')]
    images = [i for i in images if image_name_match(i, image_name_filters)]
    for docker_image in images:
        singularity_image = osp.join(bwf_dir, docker_image.replace('/', '_').replace(':','_') + '.sqsh')
        print('Creating image', singularity_image, 'from', docker_image, file=verbose)
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
                    subprocess.check_call(['sudo', 'singularity', 'build', singularity_image, recipe])
                    image_hash = file_hash(singularity_image)
                    open(singularity_image + '.md5', 'w').write(image_hash)
                finally:
                    subprocess.call(['sudo', 'rm', '-Rf', docker_files]) 
            finally:
                subprocess.call(['docker', 'rm', container])
        finally:
            shutil.rmtree(tmp)
        do = tempfile.NamedTemporaryFile(suffix='.tar')
    return len(images)


def download_singularity_image(build_workflows_repository, container_image):
    image_file = container_image.replace('/', '_').replace(':', '_') + '.sqsh'
    image_path = osp.join(build_workflows_repository, image_file)
    url = '%s/%s' % (default_download_url, image_file)
    print('Downloading', image_path, 'from', url)
    try:
        urlretrieve(url, image_path)
    except:
        print('Unable to update singularity image from', 
              url, 'to', image_path)
        return False
    
    try:
        urlretrieve(url + '.md5', image_path + '.md5')
    except:
        print('Unable to update singularity image hash from', 
              url + '.md5', 'to', image_path + '.md5')
        return False
    
    return True


def update_singularity_image(build_workflows_repository, container_image,
                             verbose=False):
    verbose = log.getLogFile(verbose)
    image_file = container_image.replace('/', '_').replace(':', '_') + '.sqsh'
    image_path = osp.join(build_workflows_repository, image_file)
    if osp.exists(image_path):
        hash_file = image_file + '.md5'
        hash_path = image_path + '.md5'
        if osp.exists(hash_path):
            local_hash = open(hash_path).read()
            tmp = tempfile.NamedTemporaryFile()
            url = '%s/%s' % (default_download_url, hash_file)
            try:
                urlretrieve(url, tmp.name)
            except:
                print('Unable to update singularity image from', 
                      url, 'to', tmp.name)

            remote_hash = open(tmp.name).read()
            if remote_hash == local_hash:
                if verbose:
                    print('Not updating', image_path, 'which is identical to',
                          url, file=verbose)
                    
                return False
    download_singularity_image(build_workflows_repository, container_image)
    return True

    
def run_singularity(casa_distro, command, gui=False, interactive=False,
                    tmp_container=True, container_image=None, container_options=[],
                    verbose=None):
    verbose = log.getLogFile(verbose)
    
    # With --cleanenv only variables prefixd by SINGULARITYENV_ are transmitted 
    # to the container
    singularity = ['singularity', 'run', '--cleanenv']
    if gui:
        gui_options = casa_distro.get('container_gui_options')
        if gui_options:
            singularity += [osp.expandvars(i) for i in gui_options]
    for source, dest in six.iteritems(casa_distro.get('container_volumes',{})):
        source = source % casa_distro
        source = osp.expandvars(source)
        dest = dest % casa_distro
        dest = osp.expandvars(dest)
        singularity += ['--bind', '%s:%s' % (source, dest)]
        
    container_env = os.environ.copy()
    tmp_env = casa_distro.get('container_env', {})
    if gui:
        tmp_env.update(casa_distro.get('container_gui_env', {}))
    
    # Creates environment with variables prefixed by SINGULARITYENV_
    # with --cleanenv only these variables are given to the container
    for name, value in six.iteritems(tmp_env):
        value = value % casa_distro
        value = osp.expandvars(value)
        container_env['SINGULARITYENV_' + name] = value
    singularity += casa_distro.get('container_options', [])
    singularity += container_options
    if container_image is None:
        container_image = casa_distro.get('container_image')
        if container_image is None:
            raise ValueError('container_image is missing from casa_distro.json')
        container_image = container_image.replace('/', '_').replace(':', '_')
        container_image = osp.join(osp.dirname(osp.dirname(
            casa_distro['build_workflow_dir'])), '%s.sqsh' % container_image)
        if not osp.exists(container_image):
            raise ValueError("'%s' does not exist" % container_image)
    singularity += [container_image]
    singularity += command
    if verbose:
        print('-' * 40, file=verbose)
        print('Running singularity with the following command:', file=verbose)
        print(*("'%s'" % i for i in singularity), file=verbose)
        print('\nUsing the following environment:', file=verbose)
        for n, v in six.iteritems(container_env):
            print('    %s=%s' % (n, v), file=verbose)
        print('-' * 40, file=verbose)
    check_call(singularity, env=container_env)

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

