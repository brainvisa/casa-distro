# coding: utf-8 

from __future__ import print_function

import os.path as osp
import re
import yaml
import requests
import json

from brainvisa.maker.plugins.svn import get_latest_revision
from brainvisa.maker.brainvisa_clients import read_remote_project_info
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
            latest_release_url = url_per_component[component].get('tag')
            bug_fix_svn = url.split(None,1)[1]
            vcc = get_version_control_component(
                        project_per_component[ component ],
                        component,
                        bug_fix_url
                    )
            bug_fix_revision = get_latest_revision(bug_fix_svn)
            
            bug_fix_version = read_remote_project_info(vcc.client(), bug_fix_svn)
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
                latest_release_revision = get_latest_revision(latest_release_svn)
                if latest_release_revision != bug_fix_revision:
                    latest_release_version = read_remote_project_info(vcc.client(), latest_release_svn)
                    if latest_release_version:
                        latest_release_version = latest_release_version[2]
                    latest_release_version_string = str(latest_release_version)
                    component_dict['latest_release'] = {
                        'vcs_type': vcs,
                        'vcs_url': latest_release_svn,
                        'version': latest_release_version_string,
                        'revision': latest_release_revision,
                    }
                    if verbose:
                        print('  latest_release version %s in %s (%s) with revision %s' % 
                            (str(latest_release_version), latest_release_svn, vcs,
                            latest_release_revision), file=verbose)
                        verbose.flush()
                    base_url, branch_type, branch = latest_release_svn.rsplit('/', 2)
                    versioned_latest_release_svn = '%s/%s/%s' % (base_url, 'tags', str(latest_release_version))
                    
                    if latest_release_version == bug_fix_version:
                        warning_messages.append('Version of latest_release and bug_fix are the same.')
                        new_bug_fix_version = latest_release_version.increment()
                    elif latest_release_version > bug_fix_version:
                        error_messages.append('latest_release version is higher than bug_fix version.')
                        new_bug_fix_version = bug_fix_version
                    else:
                        new_bug_fix_version = bug_fix_version
                    info_messages.append('Upgrade from version %s to version %s.' % (latest_release_version_string, new_bug_fix_version))
                    component_dict['todo'] = [
                        ['rename', latest_release_svn, versioned_latest_release_svn],
                        ['copy', bug_fix_svn, latest_release_svn],
                        ['set_version', bug_fix_svn, str(new_bug_fix_version)],
                    ]
                    latest_release_version = None
                else:
                    component_dict['latest_release'] = {
                        'vcs_type': vcs,
                        'vcs_url': latest_release_svn,
                        'version': str(bug_fix_version),
                        'revision': bug_fix_revision,
                    }
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
    print(yaml.dump(components_info_and_release_plan, default_flow_style=False), file=release_plan_file)
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
