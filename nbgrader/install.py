from __future__ import print_function, absolute_import

"""
Misc utils to deals wit installing nbgrader on a system
"""

import sys
import io
import os.path
import json
import argparse

import IPython.html.nbextensions as nbe
from IPython.utils.path import locate_profile, get_ipython_dir
from IPython.core.profiledir import ProfileDir
from IPython.utils.py3compat import cast_unicode_py2


def install(profile='default', symlink=True, user=False, prefix=None,
            verbose=False, ipython_dir=None):
    """Install and activate nbgrader on a profile
    """

    dname = os.path.dirname(__file__)
    # might want to check if already installed and overwrite if exist
    if symlink and verbose:
        print('I will try to symlink the extension instead of copying files')
    if prefix and verbose:
        print("I will install in prefix:", prefix)
    if not ipython_dir:
        nbextensions_dir = None
    else:
        nbextensions_dir = os.path.join(ipython_dir,'nbextensions')

    nbe.install_nbextension(os.path.join(dname, 'nbextensions', 'nbgrader'),
                            user=user,
                            prefix=prefix,
                            symlink=symlink,
                            nbextensions_dir=nbextensions_dir
                            )


# TODO pass prefix as argument.
def activate(profile=None, ipython_dir=None):
    """
    Manualy modify the frontend json-config to load nbgrader extension.
    """

    if not ipython_dir:
        pdir = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), profile).location
    else :
        ipython_dir = os.path.expanduser(ipython_dir)
        pdir = ProfileDir.find_profile_dir_by_name(ipython_dir, profile).location

    json_dir = os.path.join(pdir, 'nbconfig')
    json_file = os.path.join(pdir, 'nbconfig', 'notebook.json')
    json_file = os.path.expanduser(json_file)

    try:
        with io.open(json_file, 'r') as f:
            config = json.loads(f.read())
    except IOError:
        # file just don't exists yet. IPython might have never been launched.
        config = {}

    if not config.get('load_extensions', None):
        config['load_extensions'] = {}
    config['load_extensions']['nbgrader/create_assignment'] = True

    if not os.path.exists(json_dir):
        os.mkdir(json_dir)

    with io.open(json_file, 'w+') as f:
        f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))


def deactivate(profile=None, ipython_dir=None):
    """should be a matter of just unsetting the above keys
    """
    raise NotImplemented('deactivating a profile is not yet implemented.')


def main(argv=None):
    """Parse sys argv.args and install nbgrader extensions"""

    # this is what argparse does if set to None, 
    # and allows us to test this function with nose. 
    if not argv:
        argv = sys.argv[1:]

    prog = '{} -m nbgrader'.format(os.path.basename(sys.executable))
    parser = argparse.ArgumentParser(prog=prog,
                description='''Install and activate nbgrader notebook extension for a given profile ''')
    parser.add_argument('profile', nargs='?', default=None, metavar=('<profile_name>'))

    parser.add_argument("--install", help="Install nbgrader notebook extension for given profile",
                        action="store_true")

    parser.add_argument("--activate", help="Activate nbgrader notebook extension for given profile",
                        action="store_true")

    parser.add_argument("--deactivate", help="Deactivate nbgrader extension for given profile",
                        action="store_true")

    parser.add_argument("-v", "--verbose", help="Increase verbosity",
                        action='store_true')

    parser.add_argument("--user", help="Force install in user land",
                        action="store_true")

    parser.add_argument("--no-symlink", help="Do not symlink at install time, but copy the files",
                        action="store_false", dest='symlink', default=True)

    parser.add_argument("--path", help="Explicit path to the ipython-dir to use",
                        action='store', default=None)

    parser.add_argument("--prefix", help="Prefix where to install extension",
                        action='store', default=None)

    args = parser.parse_args(argv)

    help_and_exit = False
    if args.activate and args.deactivate:
        print("Cannot activate and deactivate extension as the same time", file=sys.stderr)
        help_and_exit = True

    if args.user and not args.install:
        print("--user can only be used in conjunction with the --install flag.")
        help_and_exit = True
    
    if not args.symlink and not args.install:
        print("--no-symlink can only be used in conjunction with the --install flag.")
        help_and_exit = True

    if not args.profile or help_and_exit:
        parser.print_help()
        sys.exit(1)

    if args.install:
        install( ipython_dir=args.path,
                        user=args.user,
                      prefix=args.prefix,
                     profile=args.profile,
                     symlink=args.symlink,
                     verbose=args.verbose,
                )

    if args.activate :
        activate( ipython_dir=args.path,
                      profile=args.profile) 
    if args.deactivate :
        deactivate( ipython_dir=args.path,
                        profile=args.profile) 
