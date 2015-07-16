import os
import glob
import re
import shutil
import sys
import nbgrader.apps

from textwrap import dedent
from clear_docs import run, clear_notebooks

try:
    from StringIO import StringIO # Python 2
except ImportError:
    from io import StringIO # Python 3


# get absolute path to IPython to make sure it's the same one as what is installed
# in the virtualenv
IPYTHON = os.path.join(os.path.dirname(sys.executable), 'ipython')


def autogen_command_line(root):
    """Generate command line documentation."""

    header = dedent(
        """
        ``{}``
        ========================

        ::

        """
    )

    apps = [
        'AssignApp',
        'AutogradeApp',
        'CollectApp',
        'ExtensionApp',
        'FeedbackApp',
        'FetchApp',
        'FormgradeApp',
        'ListApp',
        'NbGraderApp',
        'ReleaseApp',
        'SubmitApp',
        'ValidateApp'
    ]

    print('Generating command line documentation')
    orig_stdout = sys.stdout

    for app in apps:
        cls = getattr(nbgrader.apps, app)
        buf = sys.stdout = StringIO()
        cls().print_help(True)
        buf.flush()
        helpstr = buf.getvalue()
        helpstr = "\n".join(["    " + x for x in helpstr.split("\n")])

        name = cls.name.replace(" ", "-")
        destination = os.path.join(root, 'command_line_tools/{}.rst'.format(name))
        with open(destination, 'w') as f:
            f.write(header.format(cls.name.replace("-", " ")))
            f.write(helpstr)

    sys.stdout = orig_stdout


def autogen_config(root):
    """Generate an example configuration file"""

    header = dedent(
        """
        Configuration options
        =====================

        These options can be set in ``nbgrader_config.py``, or at the command line when you start it.
        ::

        """
    )

    print('Generating example configuration file')
    config = nbgrader.apps.NbGraderApp().generate_config_file()
    config = "\n".join(["    " + x for x in config.split("\n")])
    destination = os.path.join(root, 'config_options.rst')
    with open(destination, 'w') as f:
        f.write(header)
        f.write(config)



def build_notebooks(root):
    """Execute notebooks and convert them to rst"""
    print("Executing and converting notebooks in '{}'...".format(os.path.abspath(root)))

    cwd = os.getcwd()
    os.chdir(root)

    # hack to convert links to ipynb files to html
    for filename in sorted(glob.glob('user_guide/*.ipynb')):
        run([
            IPYTHON, 'nbconvert',
            '--to', 'rst',
            '--execute',
            '--FilesWriter.build_directory=user_guide',
            '--profile-dir', '/tmp',
            filename
        ])

        filename = os.path.splitext(filename)[0] + '.rst'
        with open(filename, 'r') as fh:
            source = fh.read()
        source = re.sub(r"<([^><]*)\.ipynb>", r"<\1.html>", source)
        with open(filename, 'w') as fh:
            fh.write(source)

    # convert examples to html
    for dirname, dirnames, filenames in os.walk('user_guide'):
        if dirname == 'user_guide':
            continue
        if dirname == 'user_guide/images':
            continue

        build_directory = os.path.join('extra_files', dirname)
        if not os.path.exists(build_directory):
            os.makedirs(build_directory)

        for filename in sorted(filenames):
            if filename.endswith('.ipynb'):
                run([
                    IPYTHON, 'nbconvert',
                    '--to', 'html',
                    "--FilesWriter.build_directory='{}'".format(build_directory),
                    '--profile-dir', '/tmp',
                    os.path.join(dirname, filename)
                ])

            else:
                shutil.copy(
                    os.path.join(dirname, filename),
                    os.path.join(build_directory, filename))

    os.chdir(cwd)


if __name__ == "__main__":
    root = os.path.abspath(os.path.dirname(__file__))
    clear_notebooks(root)
    build_notebooks(root)
    autogen_command_line(root)
    autogen_config(root)
