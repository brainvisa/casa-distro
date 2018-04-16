from __future__ import print_function

import os
import os.path as osp
import subprocess
import json
import tempfile
import shutil
import fnmatch
from subprocess import check_call, check_output

from casa_distro import six

def image_name_match(image_name, filters):
    '''
    Tests if an image name matches one of the filters.
    It uses fnmatch syntax.
    '''     
    for f in filters:
        if fnmatch.fnmatch(image_name, f):
            return True

def create_singularity_images(bwf_dir, image_name_filters = ['cati/*'], verbose=None):
    '''
    Creates singularity images by converting to docker images.
    Return the number of images processed.
    ''' 
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
        entry_point = docker_img_config.get('Entrypoint')
        cmd = docker_img_config.get('Cmd')
        if entry_point:
            runscript = entry_point
            if cmd:
                runscript += cmd
        elif cmd:
            runscript = cmd
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

%%runscript
    %s''' % (docker_files,
             docker_image,
        '\n'.join('    %s=%s' % (n, v) for n, v in six.iteritems(env)),
        'export %s' % ' '.join(env),
        ' '.join("'%s'" %i for i in runscript)),        
                    file=out)
                    out.close()
                    subprocess.check_call(['sudo', 'singularity', 'build', singularity_image, recipe])
                finally:
                    subprocess.call(['sudo', 'rm', '-Rf', docker_files]) 
            finally:
                subprocess.call(['docker', 'rm', container])
        finally:
            shutil.rmtree(tmp)
        do = tempfile.NamedTemporaryFile(suffix='.tar')
    return len(images)

def run_singularity(casa_distro, command, gui=False, interactive=False,
                    tmp_container=True, container_image=None, container_options=[],
                    verbose=None):
    singularity = ['singularity', 'exec', '--cleanenv', '--cleanenv']
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
    env = os.environ.copy()
    for name, value in six.iteritems(casa_distro.get('container_env',{})):
        value = value % casa_distro
        value = osp.expandvars(value)
        env['SINGULARITYENV_' + name] = value
    singularity += casa_distro.get('container_options', [])
    singularity += container_options
    if container_image is None:
        container_image = casa_distro.get('container_image')
        if container_image is None:
            raise ValueError('container_image is missing from casa_distro.json')
        container_image = container_image.replace('/', '_').replace(':', '_')
        container_image = osp.join(osp.dirname(osp.dirname(casa_distro['build_workflow_dir'])), '%s.sqsh' % container_image)
        if not osp.exists(container_image):
            raise ValueError("'%s' does not exist" % container_image)
    singularity += [container_image]
    singularity += command
    if verbose:
        print('-' * 40, file=verbose)
        print('Running singularity with the following command:', file=verbose)
        print(*("'%s'" % i for i in singularity), file=verbose)
        print('\nUsing the following environment:', file=verbose)
        for n, v in six.iteritems(env):
            print('    %s=%s' % (n, v), file=verbose)
        print('-' * 40, file=verbose)
    check_call(singularity, env=env)

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

