#!/usr/bin/env python

import os
import sys
import subprocess as sp
import argparse
from tempfile import mkdtemp


def echo(msg):
    print("\033[1;37m{0}\033[0m".format(msg))


def run(cmd, **kwargs):
    echo(cmd)
    return sp.check_call(cmd, shell=True, **kwargs)


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


def docs(ns, args):
    del ns  # unused
    run('git clean -fdX nbgrader/docs')
    if not WINDOWS:
        run('pytest --nbval-lax --current-env nbgrader/docs/source/user_guide/*.ipynb')
    run('python nbgrader/docs/source/build_docs.py')
    run('python nbgrader/docs/source/clear_docs.py')
    run('make -C nbgrader/docs html')
    run('make -C nbgrader/docs linkcheck')


def cleandocs(ns, args):
    del ns  # unused
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


def _run_ts_test(args, notebook=False):
    root_dir = mkdtemp(prefix="nbgrader-galata-")
    os.environ["NBGRADER_TEST_DIR"] = root_dir

    if notebook:
        os.environ["NBGRADER_TEST_IS_NOTEBOOK"] = "1"

    cmd = ['jlpm', f'test{":notebook" if notebook else ""}', '--retries=3'] + args
    run(" ".join(cmd))


def tests(ns, args):
    if ns.group == 'python':
        _run_tests(
            mark="not nbextensions", skip=ns.skip, junitxml=ns.junitxml, paralell=True)

    elif ns.group == 'nbextensions':
        _run_ts_test(args, notebook=True)

    elif ns.group =='labextensions':
        _run_ts_test(args)

    elif ns.group == 'docs':
        docs(ns)

    elif ns.group == 'all':
        _run_tests(mark=None, skip=ns.skip, junitxml=ns.junitxml)
        _run_ts_test()
        _run_ts_test(notebook=True)

    else:
        raise ValueError("Invalid test group: {}".format(ns.group))


def aftersuccess(ns, args):
    if ns.group in ('python'):
        run('codecov')
    else:
        echo('Nothing to do.')


def js(ns, args):
    run('npm install')
    run('./node_modules/.bin/bower install --config.interactive=false')
    if ns.clean:
        run('git clean -fdX nbgrader/server_extensions/formgrader/static/components')


def install(ns, args):
    if ns.group in ['docs', 'all']:
        cmd = 'pip install .[docs,tests]'
    else:
        cmd = 'pip install -e .[tests]'

    env = os.environ.copy()
    if ns.group not in ['all', 'labextensions', 'nbextensions']:
        env['SKIP_JUPYTER_BUILDER'] = '1'
    run(cmd, env=env)


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

    (ns, args) = parser.parse_known_args()
    ns.func(ns, args)
