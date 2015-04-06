import subprocess as sp
import os
import time
import sys

from textwrap import dedent

from .test_nbgrader_formgrade import TestNbgraderFormgrade

class TestNbgraderFormgradeHubAuth(TestNbgraderFormgrade):

    base_formgrade_url = "http://localhost:8000/hub/course123ABC/"
    base_notebook_url = "http://localhost:8000/user/foobar/notebooks/class_files/"

    @classmethod
    def _setup_formgrade_config(cls):
        # create config file
        with open("nbgrader_config.py", "w") as fh:
            fh.write(dedent(
                """
                c = get_config()
                c.NbGraderConfig.course_id = 'course123ABC'
                c.FormgradeApp.port = 9000
                c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
                c.HubAuth.graders = ["foobar"]
                c.HubAuth.notebook_url_prefix = "class_files"
                """
            ))

    @classmethod
    def _start_jupyterhub(cls):
        with open(os.path.join(cls.tempdir, "jupyterhub_config.py"), "w") as fh:
            fh.write(dedent(
                """
                c = get_config()
                c.JupyterHub.authenticator_class = 'nbgrader.tests.fakeuser.FakeUserAuth'
                c.JupyterHub.spawner_class = 'nbgrader.tests.fakeuser.FakeUserSpawner'
                """
            ))

        os.environ['CONFIGPROXY_AUTH_TOKEN'] = 'foo'
        cls.jupyterhub = cls._start_subprocess(
            ["jupyterhub"],
            shell=False,
            stdout=None,
            stderr=None,
            cwd=cls.tempdir)

        time.sleep(1)

    @classmethod
    def _start_formgrader(cls):
        cls._start_jupyterhub()

        token = sp.check_output(['jupyterhub', 'token'], cwd=cls.tempdir).decode().strip()
        os.environ['JPY_API_TOKEN'] = token
        os.environ['CONFIGPROXY_AUTH_TOKEN'] = 'foo'
        super(TestNbgraderFormgradeHubAuth, cls)._start_formgrader()

    @classmethod
    def _stop_jupyterhub(cls):
        cls.jupyterhub.terminate()

        # wait for the formgrader to shut down
        for i in range(10):
            retcode = cls.jupyterhub.poll()
            if retcode is not None:
                break
            time.sleep(0.1)

        # not shutdown, force kill it
        if retcode is None:
            cls.jupyterhub.kill()

    @classmethod
    def _stop_formgrader(cls):
        super(TestNbgraderFormgradeHubAuth, cls)._stop_formgrader()
        cls._stop_jupyterhub()

    def test_00_login(self):
        # this test name is a hack to make sure it is always run first, because
        # we need to actually authenticate, otherwise all the tests will just
        # be met with a login page
        base = super(TestNbgraderFormgradeHubAuth, self).base_formgrade_url
        self.browser.get(base)
        self._wait_for_element("username_input")
        self._check_url("http://localhost:8000/hub/login?next={}".format(self.formgrade_url()))

        # fill out the form
        self.browser.find_element_by_id("username_input").send_keys("foobar")
        self.browser.find_element_by_id("login_submit").click()

        # check the url
        self._wait_for_gradebook_page("assignments")


class TestNbgraderHubToken(TestNbgraderFormgradeHubAuth):

    @classmethod
    def _setup_formgrade_config(cls):
        # create config file
        with open("nbgrader_config.py", "w") as fh:
            fh.write(dedent(
                """
                c = get_config()
                c.NbGraderConfig.course_id = 'course123ABC'
                c.FormgradeApp.port = 9000
                c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
                c.HubAuth.graders = ["foobar"]
                c.HubAuth.notebook_url_prefix = "class_files"
                c.HubAuth.proxy_token = 'foo'
                c.HubAuth.generate_hubapi_token = True
                c.HubAuth.hub_db = '{}/jupyterhub.sqlite'
                """.format(cls.tempdir)
            ))

    @classmethod
    def _start_formgrader(cls):
        cls._start_jupyterhub()
        # Call parent's parent's _start_formgrader method.
        super(TestNbgraderFormgradeHubAuth, cls)._start_formgrader()


class TestFormgradeCustomHubURL(TestNbgraderFormgradeHubAuth):

    base_formgrade_url = "http://localhost:8000/hub/grader/"

    @classmethod
    def _setup_formgrade_config(cls):
        # create config file
        with open("nbgrader_config.py", "w") as fh:
            fh.write(dedent(
                """
                c = get_config()
                c.NbGraderConfig.course_id = 'course123ABC'
                c.FormgradeApp.port = 9000
                c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
                c.HubAuth.graders = ["foobar"]
                c.HubAuth.notebook_url_prefix = "class_files"
                c.HubAuth.remap_url = '/hub/grader'
                """
            ))

del TestNbgraderFormgrade

# don't run tests if it's not python 3
if sys.version_info[0] != 3:
    del TestNbgraderFormgradeHubAuth
    del TestNbgraderHubToken
    del TestFormgradeCustomHubURL
