import time
import os
import subprocess as sp

from textwrap import dedent
from nbgrader.tests import start_subprocess, copy_coverage_files

# to add a new manager for the tests, you MUST add it to this list of classes
__all__ = [
    "DefaultManager",
    "HubAuthManager",
    "HubAuthTokenManager",
    "HubAuthCustomUrlManager",
    "HubAuthSSLManager"
]

class DefaultManager(object):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NoAuth.nbserver_port = 9001
        c.FormgradeApp.port = 9000
        """
    )

    base_formgrade_url = "http://localhost:9000/"
    base_notebook_url = "http://localhost:9001/notebooks/"

    def __init__(self, tempdir, startup_wait=5, shutdown_wait=5):
        self.tempdir = tempdir
        self.startup_wait = startup_wait
        self.shutdown_wait = shutdown_wait
        self.formgrader = None
        self.jupyterhub = None
        self.env = os.environ.copy()

    def _write_config(self):
        with open("nbgrader_config.py", "w") as fh:
            fh.write(self.nbgrader_config.format(tempdir=self.tempdir))

    def _start_jupyterhub(self):
        pass

    def _start_formgrader(self):
        self.formgrader = start_subprocess(["nbgrader", "formgrade"], env=self.env)
        time.sleep(self.startup_wait)

    def start(self):
        self._write_config()
        self._start_jupyterhub()
        self._start_formgrader()

    def _stop_formgrader(self):
        self.formgrader.terminate()

        # wait for the formgrader to shut down
        for i in range(int(self.shutdown_wait / 0.1)):
            retcode = self.formgrader.poll()
            if retcode is not None:
                break
            time.sleep(0.1)

        # not shutdown, force kill it
        if retcode is None:
            self.formgrader.kill()

    def _stop_jupyterhub(self):
        pass

    def stop(self):
        self._stop_formgrader()
        self._stop_jupyterhub()
        copy_coverage_files()


class HubAuthManager(DefaultManager):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NbGrader.course_id = 'course123ABC'
        c.FormgradeApp.port = 9000
        c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
        c.HubAuth.graders = ["foobar"]
        c.HubAuth.notebook_url_prefix = "class_files"
        """
    )

    jupyterhub_config = dedent(
        """
        c = get_config()
        c.JupyterHub.authenticator_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserAuth'
        c.JupyterHub.spawner_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserSpawner'
        c.JupyterHub.log_level = "WARN"
        """
    )

    base_url = "http://localhost:8000"
    base_formgrade_url = "http://localhost:8000/hub/nbgrader/course123ABC/"
    base_notebook_url = "http://localhost:8000/user/foobar/notebooks/class_files/"

    def _write_config(self):
        super(HubAuthManager, self)._write_config()
        pth = os.path.join(self.tempdir, "jupyterhub_config.py")
        with open(pth, "w") as fh:
            fh.write(self.jupyterhub_config.format(tempdir=self.tempdir))

    def _start_jupyterhub(self, configproxy_auth_token='foo'):
        self.env['CONFIGPROXY_AUTH_TOKEN'] = configproxy_auth_token
        self.jupyterhub = start_subprocess(
            ["jupyterhub"],
            cwd=self.tempdir,
            env=self.env)

        time.sleep(self.startup_wait)

    def _start_formgrader(self, configproxy_auth_token='foo'):
        print("Getting token from jupyterhub")
        token = sp.check_output(['jupyterhub', 'token'], cwd=self.tempdir).decode().strip()
        self.env['JPY_API_TOKEN'] = token
        self.env['CONFIGPROXY_AUTH_TOKEN'] = configproxy_auth_token
        super(HubAuthManager, self)._start_formgrader()

    def _stop_jupyterhub(self):
        self.jupyterhub.terminate()

        # wait for the formgrader to shut down
        for i in range(int(self.shutdown_wait / 0.1)):
            retcode = self.jupyterhub.poll()
            if retcode is not None:
                break
            time.sleep(0.1)

        # not shutdown, force kill it
        if retcode is None:
            self.jupyterhub.kill()

        # remove database and cookie secret
        os.remove(os.path.join(self.tempdir, "jupyterhub.sqlite"))
        os.remove(os.path.join(self.tempdir, "jupyterhub_cookie_secret"))


class HubAuthTokenManager(HubAuthManager):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NbGrader.course_id = 'course123ABC'
        c.FormgradeApp.port = 9000
        c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
        c.HubAuth.graders = ["foobar"]
        c.HubAuth.notebook_url_prefix = "class_files"
        c.HubAuth.proxy_token = 'foo'
        c.HubAuth.generate_hubapi_token = True
        c.HubAuth.hub_db = '{tempdir}/jupyterhub.sqlite'
        """
    )

    def _start_formgrader(self):
        super(HubAuthManager, self)._start_formgrader()


class HubAuthCustomUrlManager(HubAuthManager):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NbGrader.course_id = 'course123ABC'
        c.FormgradeApp.port = 9000
        c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
        c.HubAuth.graders = ["foobar"]
        c.HubAuth.notebook_url_prefix = "class_files"
        c.HubAuth.remap_url = '/hub/grader'
        """
    )

    base_formgrade_url = "http://localhost:8000/hub/grader/"

class HubAuthSSLManager(HubAuthManager):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NbGrader.course_id = 'course123ABC'
        c.FormgradeApp.ip = '127.0.0.1'
        c.FormgradeApp.port = 9000
        c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
        c.HubAuth.graders = ["foobar"]
        c.HubAuth.notebook_url_prefix = "class_files"
        c.HubAuth.hub_base_url = "https://localhost:8000"
        """
    )

    jupyterhub_config = dedent(
        """
        c = get_config()
        c.JupyterHub.authenticator_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserAuth'
        c.JupyterHub.spawner_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserSpawner'
        c.JupyterHub.ssl_cert = '{tempdir}/jupyterhub_cert.pem'
        c.JupyterHub.ssl_key = '{tempdir}/jupyterhub_key.pem'
        c.JupyterHub.log_level = "WARN"
        """
    )

    base_url = "https://localhost:8000"
    base_formgrade_url = "https://localhost:8000/hub/nbgrader/course123ABC/"
    base_notebook_url = "https://localhost:8000/user/foobar/notebooks/class_files/"

    def _start_jupyterhub(self, *args, **kwargs):
        sp.check_call([
            "openssl",
            "req", "-x509",
            "-newkey", "rsa:2048",
            "-keyout", "{}/jupyterhub_key.pem".format(self.tempdir),
            "-out", "{}/jupyterhub_cert.pem".format(self.tempdir),
            "-days", "1",
            "-nodes",
            "-batch"
        ], cwd=self.tempdir)

        super(HubAuthSSLManager, self)._start_jupyterhub(*args, **kwargs)
