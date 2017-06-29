# coding: utf-8 

from __future__ import print_function

import os.path as osp
import re
import yaml
import requests
import json

import brainvisa.maker.svn as svn_client
from brainvisa.maker.svn import svn_rename, svn_copy, svn_update_version_info, \
                                svn_get_latest_revision
from brainvisa.maker.brainvisa_clients import find_remote_project_info, \
                                              read_remote_project_info
from brainvisa.maker.brainvisa_projects import url_per_component, project_per_component
from brainvisa.maker.brainvisa_client_components import \
                                                get_version_control_component, \
                                                BranchType
                                            
cmake_set_regexp = re.compile(r'set\(\s*([^\s]+)\s+(.*)\s*\)')
def parse_cmake_variables(filename):
    result = {}
    for line in open(osp.join(build_dir, 'bv_maker.cmake')):
        match = cmake_set_regexp.search(line)
        if match:
            var = match.group(1)
            value = match.group(2)
            try:
                i = value.index(' CACHE ')
                value = value[:i]
            except ValueError:
                pass
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            result[var] = value
    return result

def convert_github_url_to_svn(url):
    if url.startswith('git'):
        git, url, branch = url.split()[:3]
        branch_type, branch= (['branch'] + branch.split(':',1))[-2:]
        print(git, url, branch_type, branch)
        if branch_type == 'tag':
            branch_type = 'tags'
        else:
            branch_type = 'branches'
        url = 'svn %s/%s/%s' % (url, branch_type, branch)
        vcs = 'git'
    else:
        vcs = 'svn'
    return url, vcs

def inspect_components_and_create_release_plan(components, verbose=None):
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
           revision: <revision> # The Subversion revision or Git changeset
                                # of the latest_release branch.
           version: <version>   # The version of the component declared 
                                # in project_info.cmake or info.py
         bug_fix: # information about the bug_fix branch
           vcs_type: <vcs> # Can be 'svn' if component uses Subversion or
                           # 'git' for Git.
           vcs_url: <url> # URL of component source branch
           revision: <revision> # The Subversion revision or Git changeset
                                # of the bug_fix branch.
           version: <version>   # The version of the component declared 
                                # in project_info.cmake or info.py
         todo: # list of actions to perform for this component, possible
               # actions are :
           - [rename <source_url> <dest_url>]
           - [copy <source_url> <dest_url>]
           - [set_version <version> <url>]
        info_messages: # Information messages about the component
        warning_messages: # Messages indicating that a manager should pay
                          # attention and double check to the component status
        error_messages: # Message saying that something is wrong with the component,
                        # a manager must investigate and fix the problem.
    """
    from brainvisa.maker.version_number import VersionNumber
    
    if not components:
        components = list(url_per_component)
    components_info_and_release_plan = {}
    for component in components:
        if verbose:
            print('Inspecting component', component, file=verbose)
            verbose.flush()
        bug_fix_url = url_per_component[component].get('bug_fix')
        component_dict = components_info_and_release_plan.setdefault(project_per_component[component],{}).setdefault(component,{})
        info_messages = []
        warning_messages = []
        error_messages = []
        if bug_fix_url:
            url, vcs = convert_github_url_to_svn(bug_fix_url[0])
            bug_fix_url = (url,) + bug_fix_url[1:]
            latest_release_url = url_per_component[component].get('latest_release')
            bug_fix_svn = url.split(None,1)[1]
            bug_fix_revision = svn_get_latest_revision(bug_fix_svn)
            
            bug_fix_version = read_remote_project_info(svn_client, bug_fix_svn)
            if bug_fix_version:
                bug_fix_version = bug_fix_version[2]
            component_dict['bug_fix'] = {
                'vcs_type': vcs,
                'vcs_url': bug_fix_svn,
                'version': str(bug_fix_version),
                'revision': bug_fix_revision,
            }
            if verbose:
                print('  bug_fix version %s in %s (%s) with revision %s' % 
                      (str(bug_fix_version), bug_fix_svn, vcs,
                       bug_fix_revision), file=verbose)
                verbose.flush()
            if latest_release_url:
                url, vcs = convert_github_url_to_svn(latest_release_url[0])
                latest_release_url = (url,) + latest_release_url[1:]
                latest_release_svn = url.split(None,1)[1]
                
                if svn_client.svn_exists(latest_release_svn):
                    latest_release_exist = True
                else:
                    warning_messages.append('latest_release tag is undefined.')
                    latest_release_exist = False
                
                latest_release_revision = svn_get_latest_revision(latest_release_svn)
                if latest_release_revision != bug_fix_revision:
                    latest_release_version = read_remote_project_info(
                        svn_client, latest_release_svn)
                    if latest_release_version:
                        latest_release_version = latest_release_version[2]
                    component_dict['latest_release'] = {
                        'vcs_type': vcs,
                        'vcs_url': latest_release_svn,
                        'version': str(latest_release_version),
                        'revision': latest_release_revision,
                    }
                    
                else:
                   latest_release_version = bug_fix_version
                   component_dict['latest_release'] = {
                        'vcs_type': vcs,
                        'vcs_url': latest_release_svn,
                        'version': str(latest_release_version),
                        'revision': bug_fix_revision,
                    } 
                
                if latest_release_revision < bug_fix_revision \
                    or not latest_release_exist:
                    if verbose:
                        print('  latest_release version %s in %s (%s) with revision %s' % 
                            (str(latest_release_version), latest_release_svn, vcs,
                            latest_release_revision), file=verbose)
                        verbose.flush()
                    base_url, branch_type, branch = latest_release_svn.rsplit('/', 2)
                    versioned_latest_release_svn = '%s/%s/%s' % (base_url, 'tags', str(latest_release_version))
                    
                    if svn_client.svn_exists(versioned_latest_release_svn):
                        warning_messages.append('Version of latest_release ' \
                            'tag already exists as a version tag %s.' \
                        % str(latest_release_version))
                    
                    if latest_release_version == bug_fix_version:
                        warning_messages.append('Version of latest_release and bug_fix are the same.')
                        new_bug_fix_version = VersionNumber(latest_release_version).increment()
                    elif latest_release_version > bug_fix_version:
                        error_messages.append('latest_release version is higher than bug_fix version.')
                        new_bug_fix_version = bug_fix_version
                    else:
                        new_bug_fix_version = bug_fix_version
                    info_messages.append('Upgrade from version %s to version %s.' % (str(latest_release_version), new_bug_fix_version))
                    
                    component_dict['todo'] = []
                    
                    if latest_release_exist:
                        component_dict['todo'].append(
                            ['rename', latest_release_svn, versioned_latest_release_svn]
                        )
                    
                    component_dict['todo'] += [
                        ['set_version', bug_fix_svn, str(new_bug_fix_version)],
                        ['copy', bug_fix_svn, latest_release_svn],
                        #['merge', latest_release_svn, bug_fix_svn, 
                                  #str(bug_fix_revision) + ':HEAD']
                    ]
                    latest_release_version = None
                    
                else:
                    if verbose:
                        print('  latest_release identical to bug_fix in %s (%s) with revision %s' % 
                              (latest_release_svn, vcs, latest_release_revision), file=verbose)
                        verbose.flush()
            else:
                warning_messages.append('No latest_release branch.')                
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

def publish_release_plan_on_wiki(login, password, release_plan_file):
    '''
    '''
    wiki_url = 'https://bioproj.extra.cea.fr/redmine/projects/catidev/wiki/Release_plan.json'

    release_plan = yaml.load(open(release_plan_file))
    next_casa_version = release_plan['casa']['casa-distro']['bug_fix']['version']
    content = ['''h1. Release plan for casa-distro %s

This is a test page whose content is automatically generated by @casa_distro@ script.

|_. Project |_. Component |_. latest_release |_. bug_fix |_. todo |_. Comments |''' % next_casa_version]
    modified = []
    unmodified = []
    color = ''
    for project in sorted(release_plan):
        for component in sorted(release_plan[project]):
            bug_fix = release_plan[project][component].get('bug_fix')
            if bug_fix is not None:
                bug_fix = '"%s":%s' % (bug_fix.get('version', 'none'), bug_fix.get('vcs_url', 'unknown'))
            else:
                bug_fix = ''
            latest_release = release_plan[project][component].get('latest_release')
            if latest_release is not None:
                latest_release = '"%s":%s' % (latest_release.get('version', 'none'), latest_release.get('vcs_url', 'unknown'))
            else:
                latest_release = ''
            todo = ('yes' if release_plan[project][component].get('todo') else 'no')
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
            elif todo == 'yes':
                color = '#a5d6a7'
            else:
                color = '#b0bec5'
            content.append('|-{{background:{0}}}. {1} |-{{background:{0}}}. _{2}_ |-{{background:{0}}}. {3} |-{{background:{0}}}. {4} |-{{background:{0}}}. {5} |-{{background:{0}}}. {6} |'.format(
                color, 
                project, 
                component,
                latest_release,
                bug_fix,
                todo,
                comments))
    content = '\n'.join(content)
    
    print(content)
    
    r = requests.put(wiki_url, auth=(login, password), json={'wiki_page':{'text': content}})
    r.raise_for_status()

class FailOn:
    NONE = 0
    WARNING = 1
    ERROR = 2

def apply_release_plan(release_plan_file, dry=False, 
                       fail_on=FailOn.WARNING | FailOn.ERROR, verbose=None):
    ''' Apply a yaml release plan file
    '''
    import os, string
    
    if not os.path.exists(release_plan_file):
        raise RuntimeError('Release plan %s file does not exists or is not ' \
                           'accessible' % release_plan_file)
        
    release_plan = yaml.load(open(release_plan_file))
    #next_casa_version = release_plan['casa']['casa-distro']['bug_fix']['version']
    
    # First check if it remains errors or warnings
    for project in sorted(release_plan):
        for component in sorted(release_plan[project]):
            vcs_missing_info = False
            todo = release_plan[project][component].get('todo', [])
            infos = release_plan[project][component].get('info_messages', [])
            warnings = release_plan[project][component].get('warning_messages', [])
            errors = release_plan[project][component].get('error_messages', [])
            
            # Check that both bug_fix and latest_release have available infos
            for b in ('bug_fix', 'latest_release'):
                info = release_plan[project][component].get(b)
                if info is not None:
                    version = info.get('version')
                    url = info.get('vcs_url')
                    
                    if len(todo) > 0: 
                        if version is None:
                            raise RuntimeError('Missing %s version for ' \
                                'component %s' % (b, component))
                        if url is None:
                            raise RuntimeError('Missing %s url for ' \
                                'component %s' % (b, component))
                else:
                    if len(todo) > 0:
                        raise RuntimeError('Missing %s version control ' \
                            'information for component %s' % (b, component))
            
            # Check that it does not remain errors and warnings/cmnorsu 
            if len(todo) > 0:
                if (fail_on & FailOn.ERROR) and (len(errors) > 0):
                    raise RuntimeError('Remaining error messages for ' \
                        'component %s' % component)
                if (fail_on & FailOn.WARNING) and (len(warnings) > 0):
                    raise RuntimeError('Remaining warning messages for ' \
                        'component %s' % component)
                if len(infos) < 1:
                    raise RuntimeError('Missing info messages for ' \
                        'component %s (at least one is required)' % component)
                
    for project in sorted(release_plan):
        for component in sorted(release_plan[project]):
            todo = release_plan[project][component].get('todo', [])
            infos = release_plan[project][component].get('info_messages', [])

            for c in todo:
                if verbose:
                    print('RUNNING COMMAND' + (' (DRY)' if dry else '') + ':',
                          *c, file=verbose)
                    verbose.flush()
                
                if not dry:
                    if c[0] == 'rename':
                        svn_client.svn_rename(c[1], c[2], message = infos[0])
                    elif c[0] == 'copy':
                        svn_client.svn_copy(c[1], c[2], message = infos[0])
                    elif c[0] == 'set_version':
                        project_info_url = find_remote_project_info(svn_client,
                                                                    c[1])
                        #if verbose:
                            #print('found project info url:', project_info_url, file=verbose)
                            #verbose.flush()                            
                        svn_client.svn_update_version_info(project_info_url,
                                                           c[2], 
                                                           message=infos[0])
                    elif c[0] == 'merge':
                        revision_range = string.split(c[2], ':') \
                                         if len(c) > 2 else None
                        svn_client.svn_merge(c[1], c[2],
                                             revision_range=revision_range)
                        