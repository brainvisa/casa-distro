# -*- coding: utf-8 -*-
#
# SOMA documentation build configuration file, created by
# sphinx-quickstart on Wed Sep  4 12:18:01 2013.
#
# This file is execfile()d with the current directory set to its containing
# dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

from __future__ import absolute_import, print_function

import datetime
import os
import sys
from distutils.version import LooseVersion
import subprocess

import sphinx
if LooseVersion(sphinx.__version__) < LooseVersion('1'):
    raise RuntimeError('Need sphinx >= 1 for autodoc to work correctly')


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('sphinxext'))

# -- General configuration -----------------------------------------------

# We load the release info into a dict by explicit execution
release_info = {}
finfo = os.path.join('..', '..', 'python', 'casa_distro', 'info.py')
with open(finfo) as f:
    exec(compile(f.read(), finfo, 'exec'), release_info)

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
try:
    # try napoleon which replaces numpydoc (and googledoc),
    # comes with sphinx 1.2
    import sphinx.ext.napoleon
    napoleon = 'sphinx.ext.napoleon'
except ImportError:
    # not available, fallback to numpydoc
    napoleon = 'numpy_ext.numpydoc'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    # 'sphinx.ext.imgmath',
    'sphinx.ext.ifconfig',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    napoleon,
    'sphinx.ext.extlinks',
]

# Remove some numpy-linked warnings
numpydoc_show_class_members = False

# Generate autosummary even if no references
autosummary_generate = True

# Autodoc of class members
# autodoc_default_flags = ['members', 'inherited-members']
autodoc_default_flags = ['members']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
# source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'CASA-DISTRO'
copyright = (u'2017-%d' % datetime.date.today().year
             + u', %(AUTHOR)s <%(AUTHOR_EMAIL)s>' % release_info)

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = release_info['__version__']
# The full version, including alpha/beta/rc tags.
release = version

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
# today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
# unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_patterns = [
    'examples',
    "_themes/scikit-learn/static/ML_MAPS_README.rst",
    '_build',
    '**.ipynb_checkpoints'
] + templates_path

# The reST default role (used for this markup: `text`) to use for all
# documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ['_themes']

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = "CASA-Distro - BrainVisa / CATI development distribution"

# A shorter title for the navigation bar.  Default is the same as html_title.
html_short_title = "CASA-Distro"

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
# html_logo = "nsap_logo/nsap.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_style = 'custom.css'
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
html_use_modindex = False

# If false, no index is generated.
html_use_index = False

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'CASA-Distro-doc'


# -- Options for LaTeX output --------------------------------------------

# The paper size ('letter' or 'a4').
# latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
# latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples (source start
# file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ('index', 'casa_distro.tex', u'CASA-Distro Documentation',
     u'some people', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# Additional stuff for the LaTeX preamble.
# latex_preamble = ''

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_use_modindex = True

bv_cmake_version = '1.0'
swf_version = '1.0'
bv_web_version = '5.0'
try:
    from brainvisa.maker import version as bv_cmake_v
    bv_cmake_version = '%s.%s' % (bv_cmake_v.version_major,
                                  bv_cmake_v.version_minor)
except ImportError:
    pass
try:
    from soma_workflow import info as swf_v
    swf_version = '%s.%s' % (swf_v.version_major, swf_v.version_minor)
except ImportError:
    pass
try:
    from soma import aims
    bv_web_version = '%s.%s' % aims.version()
except ImportError:
    pass

# Example configuration for intersphinx: refer to the Python standard library.
# intersphinx_mapping = {'http://docs.python.org/': None}

extlinks = {
    'bv-cmake': ('../brainvisa-cmake-' + bv_cmake_version + '/%s',
                 'brainvisa cmake '),
    'soma-workflow': ('../soma-workflow-' + swf_version + '/sphinx/%s',
                      'Soma-Workflow '),
    'bv': ('../web-' + bv_web_version + '/%s', 'axon '),
}

# generate help

help = subprocess.check_output(['casa_distro', 'help', 'format=rst', 'full=1'])
with open('casa_distro_command_help.rst', 'w') as f:
    f.write(help.decode('utf-8'))
help = subprocess.check_output(['casa_distro_admin', 'help', 'format=rst',
                                'full=1'])
with open('casa_distro_admin_command_help.rst', 'w') as f:
    f.write(help.decode('utf-8'))
help = subprocess.check_output(['bv', '-h'])
with open('bv_command_help.rst', 'w') as f:
    f.write(help.decode('utf-8'))
