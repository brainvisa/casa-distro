# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import os.path as osp
import re
import yaml
import subprocess
import time

from casa_distro.log import verbose_file
import brainvisa.maker.svn as svn_client
from brainvisa.maker.svn import svn_rename, svn_copy, svn_update_version_info, \
                                svn_get_latest_revision, svn_delete
from brainvisa.maker.brainvisa_clients import find_remote_project_info, \
                                              read_remote_project_info
from brainvisa.maker.brainvisa_projects import url_per_component, project_per_component
from brainvisa.maker.brainvisa_client_components import \
                                                get_version_control_component, \
                                                BranchType
       
       
def git_get_changeset(url, branch):
    cmd = ['git', 'ls-remote', url, branch]
    result = subprocess.check_output(cmd)
    if result:
        return result.split()[0]


def convert_github_url_to_svn(url):
    if url.startswith('git'):
        # Due to a bug/feature in github API, the default branch must be 
        # accessed through keyword trunk, otherwise svn commit may fail.
        # So it is necessary to access using trunk keyword to default branch.
        git, url, branch = url.split()[:3]
        branch_type, branch= (['branch'] + branch.split(':',1))[-2:]
        print(git, url, branch_type, branch)
        if branch_type == 'default':
            branch_spec = [url, 'trunk']
        elif branch_type == 'tag':
            branch_spec = [url, 'tags', branch]
        else:
            branch_spec = [url, 'branches', branch]

        vcs = 'git'
        svn_url = '%s' % '/'.join(branch_spec)
        vcs_url = (url[:-4] if url.endswith('.git') else url) + '/tree/' + branch
        git_base_url = url
    else:
        vcs = 'svn'
        svn_url = url.split(None, 1)[1]
        vcs_url = svn_url
        git_base_url = None
    return svn_url, vcs, vcs_url, git_base_url

def inspect_components_and_create_release_plan(components, decisions=None, verbose=None):
    """
    Returns a dictionary containing information about component sources state
    and what to do during casa-distro creation. This dictionary has the 
    following structure (in YAML style):
    <project>: # name of a brainvisa-cmake project (as defined in
               # components_definition.py)
       <component>: # name of a brainvisa-cmake component
         latest_release: # information about the latest release branch
           vcs_type: <vcs> # Can be 'svn' if component uses Subversion or
                           # 'git' for Git.
           vcs_url: <url> # URL of component source branch
           svn_url: <url> # Subversion URL of component source branch
           revision: <revision> # The Subversion revision or Git changeset
                                # of the latest_release branch.
           version: <version>   # The version of the component declared 
                                # in project_info.cmake or info.py
         bug_fix: # information about the bug_fix branch
           vcs_type: <vcs> # Can be 'svn' if component uses Subversion or
                           # 'git' for Git.
           vcs_url: <url> # URL of component source branch
           svn_url: <url> # Subversion URL of component source branch
           revision: <revision> # The Subversion revision or Git changeset
                                # of the bug_fix branch.
           version: <version>   # The version of the component declared 
                                # in project_info.cmake or info.py
         release_candidate: # information about the release_candidate branch
           vcs_type: <vcs> # Can be 'svn' if component uses Subversion or
                           # 'git' for Git.
           vcs_url: <url> # URL of component source branch
           svn_url: <url> # Subversion URL of component source branch
         todo: # list of actions to perform for this component, possible
           # actions are :
           # - [rename <source_url> <dest_url>]
           # - [copy <source_url> <dest_url>]
           # - [set_version <version> <url>]
           release_candidate: # list of actions to create release candidate branch 
           latest_release: # list of actions to create latest releasebranch 
        info_messages: # Information messages about the component
        warning_messages: # Messages indicating that a manager should pay
                          # attention and double check to the component status
        error_messages: # Message saying that something is wrong with the component,
                        # a manager must investigate and fix the problem.
    """
    from brainvisa.maker.version_number import VersionNumber
    
    if not components:
        components = list(url_per_component)
    if decisions is None:
        components_to_ignore = set()
        projects_to_ignore = set()
    else:
        components_to_ignore = set(decisions.get('ignore', {}).get('component', []))
        projects_to_ignore = set(decisions.get('ignore', {}).get('project', []))
        
    components_info_and_release_plan = {}
    verbose = verbose_file(verbose)
    for component in components:
        if verbose:
            print('Inspecting component', component, file=verbose)
            verbose.flush()
        project = project_per_component[component]
        bug_fix_url = url_per_component[component].get('bug_fix')
        component_dict = components_info_and_release_plan.setdefault(project,{}).setdefault(component,{})
        if component in components_to_ignore or project in projects_to_ignore:
            if verbose:
                print('  ignored by decision', file=verbose)
                verbose.flush()
            component_dict['info_messages'] = ['Ignored by decision']
            continue
        info_messages = []
        warning_messages = []
        error_messages = []
        if bug_fix_url:
            url, vcs, vcs_url, git_base_url = convert_github_url_to_svn(bug_fix_url[0])
            bug_fix_url = (url,) + bug_fix_url[1:]
            latest_release_url = url_per_component[component].get('latest_release')
            bug_fix_svn = url
            
            if vcs == 'git':
                bug_fix_revision = git_get_changeset(git_base_url, 'master')
            else:
                bug_fix_revision = svn_get_latest_revision(bug_fix_svn)
            
            bug_fix_version = read_remote_project_info(svn_client, bug_fix_svn)
            if bug_fix_version:
                bug_fix_version = bug_fix_version[2]
            component_dict['bug_fix'] = {
                'vcs_type': vcs,
                'svn_url': bug_fix_svn,
                'vcs_url': vcs_url,
                'version': str(bug_fix_version),
                'revision': bug_fix_revision,
            }
            if verbose:
                print('  bug_fix version %s in %s (%s) with revision %s' % 
                      (str(bug_fix_version), bug_fix_svn, vcs,
                       bug_fix_revision), file=verbose)
                verbose.flush()
            
            # Set release candidate branch info
            rc_dict = component_dict['release_candidate'] = component_dict['bug_fix'].copy()
            if vcs == 'git':
                rc_dict['vcs_url'] = rc_dict['vcs_url'].replace('/master', '/release_candidate')
                release_candidate_svn = rc_dict['svn_url'] = rc_dict['svn_url'].replace('/trunk', '/branches/release_candidate')
                if svn_client.svn_exists(release_candidate_svn):
                    release_candidate_revision = git_get_changeset(git_base_url, 'release_candidate')
                    rc_dict['revision'] = release_candidate_revision
                    release_candidate_version = read_remote_project_info(svn_client, release_candidate_svn)
                    if release_candidate_version:
                        release_candidate_version = release_candidate_version[2]
                        rc_dict['version'] = str(release_candidate_version)
                    else:
                        del rc_dict['version']
                else:
                    release_candidate_revision = None
                    del rc_dict['revision']
                    release_candidate_version = None
                    del rc_dict['version']
            else:
                rc_dict['vcs_url'] = rc_dict['vcs_url'].replace('/bug_fix', '/release_candidate')
                release_candidate_svn = rc_dict['svn_url'] = rc_dict['svn_url'].replace('/bug_fix', '/release_candidate')
                if svn_client.svn_exists(release_candidate_svn):
                    release_candidate_revision = svn_get_latest_revision(release_candidate_svn)
                    rc_dict['revision'] = release_candidate_revision
                    release_candidate_version = read_remote_project_info(svn_client, release_candidate_svn)
                    if release_candidate_version:
                        release_candidate_version = release_candidate_version[2]
                        rc_dict['version'] = str(release_candidate_version)
                    else:
                        del rc_dict['version']
                else:
                    release_candidate_revision = None
                    del rc_dict['revision']
                    release_candidate_version = None
                    del rc_dict['version']
            if latest_release_url:
                url, vcs, vcs_url, git_base_url = convert_github_url_to_svn(latest_release_url[0])
                latest_release_url = (url,) + latest_release_url[1:]
                latest_release_svn = url
                
                if svn_client.svn_exists(latest_release_svn):
                    latest_release_exist = True
                else:
                    warning_messages.append('latest_release tag is undefined.')
                    latest_release_exist = False
                if vcs == 'git':
                    latest_release_revision = git_get_changeset(git_base_url, 'latest_release')
                else:
                    latest_release_revision = svn_get_latest_revision(latest_release_svn)
                if latest_release_revision != bug_fix_revision:
                    latest_release_version = read_remote_project_info(
                        svn_client, latest_release_svn)
                    if latest_release_version:
                        latest_release_version = latest_release_version[2]
                    component_dict['latest_release'] = {
                        'vcs_type': vcs,
                        'svn_url': latest_release_svn,
                        'vcs_url': vcs_url,
                        'version': str(latest_release_version),
                        'revision': latest_release_revision,
                    }
                    
                else:
                   latest_release_version = bug_fix_version
                   component_dict['latest_release'] = {
                        'vcs_type': vcs,
                        'svn_url': latest_release_svn,
                        'vcs_url': vcs_url,
                        'version': str(latest_release_version),
                        'revision': bug_fix_revision,
                    } 
                
                if latest_release_revision != bug_fix_revision \
                    or not latest_release_exist:
                    if verbose:
                        print('  latest_release version %s in %s (%s) with revision %s' % 
                            (str(latest_release_version), latest_release_svn, vcs,
                            latest_release_revision), file=verbose)
                        verbose.flush()
                    base_url, branch_type, branch = latest_release_svn.rsplit('/', 2)
                    versioned_latest_release_svn = '%s/%s/%s' % (base_url, 'tags', str(latest_release_version))
                    
                    if svn_client.svn_exists(versioned_latest_release_svn):
                        if vcs == 'git':
                            versioned_latest_release_revision = git_get_changeset(git_base_url, str(latest_release_version))
                        else:
                            versioned_latest_release_revision = svn_get_latest_revision(versioned_latest_release_svn)
                    else:
                        versioned_latest_release_revision = None
                    if versioned_latest_release_revision:
                        component_dict['versioned_latest_release'] = {
                            'vcs_type': vcs,
                            'svn_url': versioned_latest_release_svn,
                            'revision': versioned_latest_release_revision,
                        }
                        if versioned_latest_release_revision != latest_release_revision and vcs != 'git':
                           error_messages.append('Version of latest_release ' \
                                                    'tag already exists as a version tag %s and they have different revisions.' \
                                                    % str(latest_release_version))
                             
                    if latest_release_version == bug_fix_version:
                        # warning_messages.append('Version of latest_release and bug_fix are the same.')
                        new_bug_fix_version = VersionNumber(latest_release_version).increment()
                    elif latest_release_version > bug_fix_version:
                        error_messages.append('latest_release version is higher than bug_fix version.')
                        new_bug_fix_version = bug_fix_version
                    else:
                        new_bug_fix_version = bug_fix_version
                    info_messages.append('Upgrade from version %s to version %s.' % (str(latest_release_version), new_bug_fix_version))
                    
                    todo_release_candidate = []
                    todo_latest_release = []
                    component_dict['todo'] = {
                        'release_candidate': todo_release_candidate,
                        'latest_release': todo_latest_release,
                    }
                    
                    if latest_release_exist:
                        if latest_release_version == release_candidate_version:
                            new_release_candidate_version = VersionNumber(release_candidate_version).increment()
                            todo_latest_release.append(['set_version', release_candidate_svn, str(new_release_candidate_version)])
                            if new_release_candidate_version == new_bug_fix_version:
                                todo_latest_release.append(['set_version', bug_fix_svn, str(new_bug_fix_version.increment())])
                            
                        if versioned_latest_release_revision:
                            todo_latest_release.append(
                                ['delete', latest_release_svn]
                            )
                        else:
                            todo_latest_release.append(
                                ['rename', latest_release_svn, versioned_latest_release_svn]
                            )
                    
                    todo_release_candidate += [
                        ['set_version', bug_fix_svn, str(new_bug_fix_version)],
                        ['copy', bug_fix_svn, release_candidate_svn],
                    ]
                    todo_latest_release += [
                        ['rename', release_candidate_svn, latest_release_svn],
                    ]
                    latest_release_version = None
                    
                else:
                    msg = 'latest_release identical to bug_fix with revision %s' % latest_release_revision
                    info_messages.append(msg)
                    if verbose:
                        print('  %s' % msg, file=verbose)
                        verbose.flush()
            else:
                warning_messages.append('No latest_release branch. The branch must be created manualy and it must be added to brainvisa-cmake in components_definition.py')
                if verbose:
                    print(component, '  no latest_release branch', file=verbose)
                    verbose.flush()
        else:
            warning_messages.append('No bug_fix branch.')
            if verbose:
                print(component, 'no bug_fix branch', file=verbose)
                verbose.flush()
        if info_messages:
            component_dict['info_messages'] = info_messages
        if warning_messages:
            component_dict['warning_messages'] = warning_messages
        if error_messages:
            component_dict['error_messages'] = error_messages
    return components_info_and_release_plan


def update_release_plan_file(erase_file, components, build_workflows_repository, verbose=None):
    '''update a release plan file by reading sources.'''    
    if components:
        components = components.split(',')
    decisions_file = osp.join(build_workflows_repository, 'release_plan_decisions.yaml')
    if osp.exists(decisions_file):
        decisions = yaml.load(open(decisions_file))
        if verbose:
            print('Using decisions file', decisions_file, file=verbose)
            verbose.flush()
    else:
        decisions = None
    release_plan_file = osp.join(build_workflows_repository, 'release_plan.yaml')
    if not erase_file and osp.exists(release_plan_file):
        release_plan = yaml.load(open(release_plan_file))
    else:
        release_plan = {}
    new_release_plan = inspect_components_and_create_release_plan(components, decisions=decisions, verbose=verbose)
    for project in sorted(new_release_plan):
        for component, component_info in sorted(new_release_plan[project].items()):
            release_plan.setdefault(project, {})[component] = component_info
    print(yaml.dump(release_plan, default_flow_style=False), file=open(release_plan_file, 'w'))
    release_plan_html = osp.join(build_workflows_repository, 'release_plan.html')
    release_plan_to_html(release_plan_file, release_plan_html)


def release_plan_to_html(release_plan_file, release_plan_html):
    '''
    Create an HTML file allowing to see the release plan in a user friendly way
    '''
    release_plan = yaml.load(open(release_plan_file))
    if 'casa' in release_plan:
        next_casa_version = release_plan['casa']['casa-distro']['bug_fix']['version']
    else:
        next_casa_version = 'unknown'
    content = ['<!DOCTYPE html>',
               '<html>',
               '<head>',
               '<meta charset="utf-8"/>',
               '<title>CASA Release Plan</title>',
               '</head>',
               '<body>',
               '<h1>Release plan automatically generated by <code>casa_distro_admin</code> script on %s.</h1>\n\n' % time.asctime()]
    decisions_file, ext = osp.splitext(release_plan_file)
    decisions_file = '%s_decisions%s' % (decisions_file, ext)
    if osp.exists(decisions_file):
        content.append('<h2>Decisions file</h2>\nFile name : %s\n<pre>\n%s\n</pre>\n' % (decisions_file, open(decisions_file).read()))
    content.append('<h2>Release plan</h2>\n\n')
    content.append('<table>\n<tr><th>Project</th><th>Component</th><th>Branchs</th><th>To do</th><th>Comments</th></tr>')
    modified = []
    unmodified = []
    color = ''
    for project in sorted(release_plan):
        for component in sorted(release_plan[project]):
            
            branches = []
            bug_fix = release_plan[project][component].get('bug_fix')
            if bug_fix is not None:
                bug_fix = '<a href="%s">%s<br>Rev: %s</a>' % (bug_fix.get('vcs_url', 'unknown'), bug_fix.get('version', 'none'), bug_fix.get('revision', 'unknown'))
            else:
                bug_fix = 'none'
            branches.append('<p><b>bug_fix</b><br>%s</p>' % bug_fix)

            release_candidate = release_plan[project][component].get('release_candidate')
            if release_candidate is not None:
                release_candidate = '<a href="%s">%s<br>Rev: %s</a>' % (release_candidate.get('vcs_url', 'unknown'), release_candidate.get('version', 'none'), release_candidate.get('revision', 'unknown'))
            else:
                release_candidate = ''
            branches.append('<p><b>release_candidate</b><br>%s</p>' % release_candidate)
            
            latest_release = release_plan[project][component].get('latest_release')
            if latest_release is not None:
                latest_release = '<a href="%s">%s<br>Rev: %s</a>' % (latest_release.get('vcs_url', 'unknown'), latest_release.get('version', 'none'), latest_release.get('revision', 'unknown'))
            else:
                latest_release = ''
            branches.append('<p><b>latest_release</b><br>%s</p>' % latest_release)
            
            branches = '\n'.join(branches)
            
            todo_rc = release_plan[project][component].get('todo',{}).get('release_candidate')
            if todo_rc:
                l = []
                for action in todo_rc:
                    l.append(action[0] + '<ul>')
                    l.extend('<li>%s</li>' % i for i in action[1:])   
                    l.append('</ul>')
                todo_rc = '\n'.join(l)
            else:
                todo_rc = 'no'
            
            todo_lr = release_plan[project][component].get('todo',{}).get('latest_release')
            if todo_lr:
                l = []
                for action in todo_lr:
                    l.append(action[0] + '<ul>')
                    l.extend('<li>%s</li>' % i for i in action[1:])   
                    l.append('</ul>')
                todo_lr = '\n'.join(l)
            else:
                todo_lr = 'no'
            
            if todo_rc != 'no' or 'todo_lr' != 'no':
                todo = '<b>release_candidate:</b><p>%s</p>\n<b>latest_release:</b><p>%s</p>\n' % (todo_rc, todo_lr)
            else:
                todo = 'no'
            infos = release_plan[project][component].get('info_messages', [])
            warnings = release_plan[project][component].get('warning_messages', [])
            errors = release_plan[project][component].get('error_messages', [])
            comments = list(infos)
            comments.extend('WARNING: %s' % i for i in warnings)
            comments.extend('ERROR: %s' % i for i in errors)
            comments = '\n'.join(comments)
            if errors:
                color = '#d50000'
            elif warnings:
                color = '#ff8a65'
            elif todo_rc != 'no':
                color = '#a5d6a7'
            else:
                color = '#b0bec5'
            content.append('<tr style="vertical-align:middle;background:{0}">\n<td>{1}</td>\n<td>{2}</td>\n<td>{3}</td>\n<td>{4}</td>\n<td>{5}</td></tr>\n'.format(
                color, 
                project, 
                component,
                branches,
                todo,
                comments))
    content += ['</table>',
                '</body>',
                '</html>']
    content = '\n'.join(content)    
    print(''.join(content), file=open(release_plan_html, 'w'))


def apply_latest_release_todo(release_plan_file, 
                              previous_run_output, dry=False, 
                              fail_on_warning=True, fail_on_error=True,
                              verbose=None):
    ''' Apply the todo list defined in a release plan file to create the latest release branches
    '''
    import os, string
    
    verbose = verbose_file(verbose)
    if not os.path.exists(release_plan_file):
        raise RuntimeError('Release plan %s file does not exists or is not ' \
                           'accessible' % release_plan_file)
        
    release_plan = yaml.load(open(release_plan_file))
    #next_casa_version = release_plan['casa']['casa-distro']['bug_fix']['version']
    
    # First check if it remains errors or warnings
    todos = []
    for project in sorted(release_plan):
        for component in sorted(release_plan[project]):
            vcs_missing_info = False
            todo = release_plan[project][component].get('todo', {}).get('latest_release', [])
            vcs_type = release_plan[project][component].get('latest_release',{}).get('vcs_type', 'svn')
            infos = release_plan[project][component].get('info_messages', [])
            warnings = release_plan[project][component].get('warning_messages', [])
            errors = release_plan[project][component].get('error_messages', [])
            
            todos.extend((i,vcs_type) for i in todo)
            # Check that both bug_fix and latest_release have available infos
            for b in ('release_candidate', 'latest_release'):
                info = release_plan[project][component].get(b)
                if info is not None:
                    version = info.get('version')
                    url = info.get('svn_url')
                    
                    if todo: 
                        if version is None:
                            raise RuntimeError('Missing %s version for ' \
                                'component %s' % (b, component))
                        if url is None:
                            raise RuntimeError('Missing %s url for ' \
                                'component %s' % (b, component))
                else:
                    if todo:
                        raise RuntimeError('Missing %s version control ' \
                            'information for component %s' % (b, component))
            
            # Check that it does not remain errors and warnings/cmnorsu 
            if todo:
                if fail_on_error and errors:
                    raise RuntimeError('Remaining error messages for ' \
                        'component %s' % component)
                if fail_on_warning and warnings:
                    raise RuntimeError('Remaining warning messages for ' \
                        'component %s' % component)
                if len(infos) < 1:
                    raise RuntimeError('Missing info messages for ' \
                        'component %s (at least one is required)' % component)
                
    commands_done = []
    if osp.exists(previous_run_output):
        cmd_re = re.compile(r'RUNNING COMMAND[^:]*:\s*(.*)')
        f = open(previous_run_output)
        line = f.readline()
        while line:
            line = line.strip()
            match = cmd_re.match(line)
            if match:
                line = f.readline()
                if not line.startswith('Impossible to apply release plan'):
                    print('!!!', match.group(1).split())
                    commands_done.append(match.group(1).split())
                else:
                    break
            else:
                line = f.readline()
    if commands_done:
        command_done_index = 0
    else:
        command_done_index = None
    
    for command, vcs_type in todos:
        if dry:
            ignore = 'dry run'
        else:
            ignore = None
        if command_done_index is not None:
            if commands_done[command_done_index] == command:
                ignore = 'already done'
                command_done_index += 1
                if command_done_index >= len(commands_done):
                    command_done_index = None
            else:
                command_done_index = None
        if verbose:
            print('RUNNING COMMAND [%s]' % vcs_type + (' (ignored, %s)' % ignore if ignore else '') + ':',
                    *command, file=verbose)
            verbose.flush()
        
        if not ignore:
            svn_options=(['--secret', 'github.secret'] if vcs_type == 'git' else [])
            if command[0] == 'rename':
                svn_client.svn_rename(command[1], command[2], svn_options=svn_options, message = infos[0])
            elif command[0] == 'copy':
                svn_client.svn_copy(command[1], command[2],  svn_options=svn_options, message = infos[0])
            elif command[0] == 'set_version':
                project_info_url = find_remote_project_info(svn_client,
                                                            command[1])
                #if verbose:
                    #print('found project info url:', project_info_url, file=verbose)
                    #verbose.flush()                            
                svn_client.svn_update_version_info(project_info_url,
                                                    command[2], 
                                                    message=infos[0],
                                                    svn_options=svn_options,
                                                    verbose=verbose)
            elif command[0] == 'merge':
                revision_range = string.split(command[2], ':') \
                                    if len(command) > 2 else None
                svn_client.svn_merge(command[1], command[2], svn_options=svn_options, 
                                        revision_range=revision_range)
            elif command[0] == 'delete':
                svn_client.svn_delete(command[1], svn_options=svn_options, message = infos[0])
            else:
                raise ValueError('Unknown command in todo for component %s: %s' % (component, command[0]))
