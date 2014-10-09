# -*- coding: utf-8 -*-
"""Release data for the nbgraer project.

Based on IPython/core/release.py from the IPython project.

"""

# nbgrader version information.  An empty _version_extra corresponds
# to a full release.  'dev' as a _version_extra string means this is a
# development version
_version_major = 0
_version_minor = 0
_version_patch = 1
_version_extra = 'dev'
# _version_extra = ''  # Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor, _version_patch]

__version__ = '.'.join(map(str, _ver))
if _version_extra:
    __version__ = __version__ + '-' + _version_extra

version = __version__
version_info = (_version_major, _version_minor, _version_patch, _version_extra)

name = 'nbgrader'

description = 'A system for assigning and grading notebooks'

author = 'Jupyter Development Team'

author_email = 'ipython-dev@scipy.org'

license = 'BSD'

url = 'https://github.com/jupyter/nbgrader'

keywords = ['Notebooks', 'Grading', 'Homework']

classifiers = [
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
]
