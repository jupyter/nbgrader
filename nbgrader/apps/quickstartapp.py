# coding: utf-8

import os
import shutil
import subprocess
import sys

from textwrap import dedent
from traitlets import Bool, default
from .baseapp import NbGrader
from .. import utils

aliases = {}
flags = {
    'force': (
        {'QuickStartApp': {'force': True}},
        dedent(
            """
            Overwrite existing files if they already exist. WARNING: this is
            equivalent to doing:

                rm -r <course_id>
                nbgrader quickstart <course_id>

            So be careful when using this flag!
            """
        )
    ),
    'f': (
        {'QuickStartApp': {'force': True}},
        dedent(
            """
            Overwrite existing files if they already exist. WARNING: this is
            equivalent to doing:

                rm -r <course_id>
                nbgrader quickstart <course_id>

            So be careful when using this flag!
            """
        )
    ),
    'autotest': (
        {'QuickStartApp': {'autotest': True}},
        dedent(
            """
            Create notebook assignments that have examples of automatic test generation via
            ### AUTOTEST and ### HASHED AUTOTEST statements.
            """
        )
    ),
}

class QuickStartApp(NbGrader):

    name = u'nbgrader-quickstart'
    description = u'Create an example class files directory with an example config file and assignment'

    aliases = aliases
    flags = flags

    examples = """
        You can run `nbgrader quickstart` just on its own from where ever you
        would like to create the example class files directory. It takes just
        one argument, which is the name of your course:

            nbgrader quickstart course101

        Note that this class name need not necessarily be the same as the
        `CourseDirectory.course_id` configuration option, however by default, the
        quickstart command will set `CourseDirectory.course_id` to be the name you give
        on the command line. If you want to use a different folder name, go
        ahead and just provide the name of the folder where your class files
        will be stored, e.g.:

            nbgrader quickstart "World Music"

        and then after running the quickstart commmand, you can edit the
        `nbgrader_config.py` file to change `CourseDirectory.course_id`.

        """

    force = Bool(False, help="Whether to overwrite existing files").tag(config=True)

    autotest = Bool(False, help="Whether to use automatic test generation in example files").tag(config=True)

    @default("classes")
    def _classes_default(self):
        classes = super(QuickStartApp, self)._classes_default()
        classes.append(QuickStartApp)
        return classes

    def _course_folder_content_exists(self, course_path):
        course_folder_content = {
            "source_dir": os.path.join(course_path, "source"),
            "config_file": os.path.join(course_path, "nbgrader_config.py")
        }
        exists = os.path.isdir(course_folder_content['source_dir']) or os.path.isfile(course_folder_content['config_file'])
        return exists

    def start(self):
        super(QuickStartApp, self).start()

        # make sure the course id was provided
        if len(self.extra_args) != 1:
            self.fail("Course id not provided. Usage: nbgrader quickstart course_id")

        # make sure it doesn't exist
        course_id = self.extra_args[0]
        course_path = os.path.abspath(course_id)

        if os.path.exists(course_path):
            if self.force:
                self.log.warning("Removing existing directory '%s'", course_path)
                utils.rmtree(course_path)
            else:
                if self._course_folder_content_exists(course_path):
                    self.fail(
                        "Directory '{}' and it's content already exists! Rerun with --force to remove "
                        "this directory first (warning: this will remove the ENTIRE "
                        "directory and all files in it.) ".format(course_path))

        # create the directory
        self.log.info("Creating directory '%s'...", course_path)

        if not os.path.isdir(course_path):
            os.mkdir(course_path)

        # populate it with an example
        self.log.info("Copying example from the user guide...")
        example = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', 'docs', 'source', 'user_guide', 'source'))
        if self.autotest:
            tests_file_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), '..', 'docs', 'source', 'user_guide', 'autotests.yml'))
            shutil.copyfile(tests_file_path, os.path.join(course_path, 'autotests.yml'))
            ignored_files = shutil.ignore_patterns("*.html", "ps1")
            shutil.copytree(example, os.path.join(course_path, "source"), ignore=ignored_files)
            os.rename(os.path.join(course_path, "source", "ps1_autotest"), os.path.join(course_path, "source", "ps1"))
        else:
            ignored_files = shutil.ignore_patterns("*.html", "autotests.yml", "ps1_autotest")
            shutil.copytree(example, os.path.join(course_path, "source"), ignore=ignored_files)

        # create the config file
        self.log.info("Generating example config file...")
        currdir = os.getcwd()
        os.chdir(course_path)
        subprocess.call([sys.executable, "-m", "nbgrader", "generate_config"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        os.chdir(currdir)
        with open(os.path.join(course_path, "nbgrader_config.py"), "r") as fh:
            config = fh.read()

        subprocess.call([sys.executable, "-m", "nbgrader", "db", "assignment", "add", "ps1"], stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)
        subprocess.call([sys.executable, "-m", "nbgrader", "db", "student", "add", "bitdiddle", "--first-name", "Ben",
                         "--last-name", "Bitdiddle"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.call([sys.executable, "-m", "nbgrader", "db", "student", "add", "hacker", "--first-name", "Alyssa",
                         "--last-name", "Hacker"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.call([sys.executable, "-m", "nbgrader", "db", "student", "add", "reasoner", "--first-name", "Louis",
                         "--last-name", "Reasoner"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        with open(os.path.join(course_path, "nbgrader_config.py"), "w") as fh:
            fh.write("c = get_config()\n\n")
            fh.write("#" * 79 + "\n")
            fh.write("# Begin additions by nbgrader quickstart\n")
            fh.write("#" * 79 + "\n")
            fh.write(dedent(
                """
                # You only need this if you are running nbgrader on a shared
                # server set up.
                c.CourseDirectory.course_id = "{}"

                c.IncludeHeaderFooter.header = "source/header.ipynb"
                """
            ).format(course_id))
            fh.write("\n")
            fh.write("#" * 79 + "\n")
            fh.write("# End additions by nbgrader quickstart\n")
            fh.write("#" * 79 + "\n\n")
            fh.write(config)

        self.log.info(
            dedent(
                """
                Done! The course files are located in '%s'.

                To get started, you can edit the source notebooks located in:

                    %s

                Once you have edited them to your satisfaction, you can create
                the student version by running `nbgrader generate_assignment ps1` from the
                '%s' directory.

                For further details, please see the full nbgrader documentation at:

                    https://nbgrader.readthedocs.io/en/stable/
                """
            ).lstrip(),
            course_path,
            os.path.join(course_path, "source", "ps1"),
            course_path)
