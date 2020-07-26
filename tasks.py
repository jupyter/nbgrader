#!/usr/bin/env python

import os
import sys
import subprocess as sp
import argparse


def echo(msg):
    print("\033[1;37m{0}\033[0m".format(msg))


def run(cmd):
    echo(cmd)
    return sp.check_call(cmd, shell=True)


try:
    from nbformat import read
except ImportError:
    echo("Warning: nbformat could not be imported, some tasks may not work")

WINDOWS = sys.platform == 'win32'


def _check_if_directory_in_path(pth, target):
    while pth != '':
        pth, dirname = os.path.split(pth)
        if dirname == target:
            return True
    return False


def docs(args):
    del args  # unused
    run('git clean -fdX nbgrader/docs')
    if not WINDOWS:
        run('pytest --nbval-lax --current-env nbgrader/docs/source/user_guide/*.ipynb')
    run('python nbgrader/docs/source/build_docs.py')
    run('python nbgrader/docs/source/clear_docs.py')
    run('make -C nbgrader/docs html')
    run('make -C nbgrader/docs linkcheck')


def cleandocs(args):
    del args  # unused
    run('python nbgrader/docs/source/clear_docs.py')


def _run_tests(mark, skip, junitxml, paralell=False):
    cmd = []
    cmd.append('pytest')
    if not WINDOWS:
        cmd.append('--cov nbgrader')
        cmd.append('--no-cov-on-fail')
    if junitxml:
        cmd.extend(['--junitxml', junitxml])
    cmd.append('-v')
    cmd.append('-x')
    if paralell:
        cmd.extend(['--numprocesses', 'auto'])
    cmd.extend(['--reruns', '4'])
#    cmd.extend(['--mypy'])

    marks = []
    if mark is not None:
        marks.append(mark)
    if skip is not None:
        marks.append("not {}".format(skip))
    if len(marks) > 0:
        cmd.append('-m "{}"'.format(" and ".join(marks)))

    run(" ".join(cmd))

    if not WINDOWS:
        run("ls -a .coverage*")
        run("coverage combine || true")


def tests(args):
    if args.group == 'python':
        _run_tests(
            mark="not nbextensions", skip=args.skip, junitxml=args.junitxml, paralell=True)

    elif args.group == 'nbextensions':
        _run_tests(mark="nbextensions", skip=args.skip, junitxml=args.junitxml)

    elif args.group == 'docs':
        docs(args)

    elif args.group == 'all':
        _run_tests(mark=None, skip=args.skip, junitxml=args.junitxml)

    else:
        raise ValueError("Invalid test group: {}".format(args.group))


def aftersuccess(args):
    if args.group in ('python', 'nbextensions'):
        run('codecov')
    else:
        echo('Nothing to do.')


def js(args):
    run('npm install')
    run('./node_modules/.bin/bower install --config.interactive=false')
    if args.clean:
        run('git clean -fdX nbgrader/server_extensions/formgrader/static/components')


def install(args):
    # The docs don't seem to build correctly if it's a symlinked install.
    if args.group == 'docs':
        cmd = 'pip install -r dev-requirements.txt .'
    else:
        cmd = 'pip install -r dev-requirements.txt -e .'
    run(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # docs
    docs_parser = subparsers.add_parser('docs')
    docs_parser.set_defaults(func=docs)

    # cleandocs
    cleandocs_parser = subparsers.add_parser('cleandocs')
    cleandocs_parser.set_defaults(func=cleandocs)

    # tests
    tests_parser = subparsers.add_parser('tests')
    tests_parser.add_argument('--group', type=str, default='all')
    tests_parser.add_argument('--skip', type=str, default=None)
    tests_parser.add_argument('--junitxml', type=str, default=None)
    tests_parser.set_defaults(func=tests)

    # aftersuccess
    aftersuccess_parser = subparsers.add_parser('aftersuccess')
    aftersuccess_parser.add_argument('--group', type=str, required=True)
    aftersuccess_parser.set_defaults(func=aftersuccess)

    # js
    js_parser = subparsers.add_parser('js')
    js_parser.add_argument('--clean', type=bool, default=True)
    js_parser.set_defaults(func=js)

    # install
    install_parser = subparsers.add_parser('install')
    install_parser.add_argument('--group', type=str, required=True)
    install_parser.set_defaults(func=install)

    args = parser.parse_args()
    args.func(args)
