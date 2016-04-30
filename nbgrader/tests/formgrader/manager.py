import time
import os
import subprocess as sp
import sys
import signal

from textwrap import dedent
from .. import start_subprocess, copy_coverage_files, get_free_ports

# to add a new manager for the tests, you MUST add it to this list of classes
__all__ = [
    "DefaultManager",
    "HubAuthManager",
    "HubAuthCustomUrlManager",
    "HubAuthNotebookServerUserManager",
    "HubAuthSSLManager"
]

class DefaultManager(object):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NoAuth.nbserver_port = {nbserver_port}
        c.FormgradeApp.port = {port}
        """
    )

    _base_url = ""
    _base_formgrade_url = "http://localhost:{port}/"
    _base_notebook_url = "http://localhost:{nbserver_port}/notebooks/"

    def __init__(self, tempdir, startup_wait=5, shutdown_wait=5):
        self.tempdir = tempdir
        self.startup_wait = startup_wait
        self.shutdown_wait = shutdown_wait
        self.formgrader = None
        self.jupyterhub = None
        self.env = os.environ.copy()

        ports = get_free_ports(5)
        self.port = ports[0]
        self.nbserver_port = ports[1]
        self.hub_port = ports[2] # not always used
        self.proxy_port = ports[3] # not always used
        self.hubapi_port = ports[4] # not always used

        print("port: {}".format(self.port))
        print("nbserver_port: {}".format(self.nbserver_port))
        print("hub_port: {}".format(self.hub_port))
        print("proxy_port: {}".format(self.proxy_port))
        print("hubapi_port: {}".format(self.hubapi_port))

        self.base_url = self._base_url.format(
            hub_port=self.hub_port)
        self.base_formgrade_url = self._base_formgrade_url.format(
            port=self.port,
            hub_port=self.hub_port)
        self.base_notebook_url = self._base_notebook_url.format(
            nbserver_port=self.nbserver_port,
            hub_port=self.hub_port)

    def _write_config(self):
        with open("nbgrader_config.py", "w") as fh:
            fh.write(self.nbgrader_config.format(
                tempdir=self.tempdir,
                port=self.port,
                nbserver_port=self.nbserver_port,
                hub_port=self.hub_port,
                hubapi_port=self.hubapi_port,
                proxy_port=self.proxy_port))

    def _start_jupyterhub(self):
        pass

    def _start_formgrader(self):
        kwargs = dict(env=self.env)
        if sys.platform == 'win32':
            kwargs['creationflags'] = sp.CREATE_NEW_PROCESS_GROUP

        self.formgrader = start_subprocess(
            [sys.executable, "-m", "nbgrader", "formgrade"],
            **kwargs)

        time.sleep(self.startup_wait)

    def start(self):
        self._write_config()
        self._start_jupyterhub()
        self._start_formgrader()

    def _stop_formgrader(self):
        if sys.platform == 'win32':
            self.formgrader.send_signal(signal.CTRL_BREAK_EVENT)
        else:
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

        self.formgrader.wait()

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
        c.FormgradeApp.port = {port}
        c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
        c.HubAuth.graders = ["foobar"]
        c.HubAuth.notebook_url_prefix = "class_files"
        c.HubAuth.proxy_port = {proxy_port}
        c.HubAuth.hubapi_port = {hubapi_port}
        c.HubAuth.hub_port = {hub_port}
        """
    )

    jupyterhub_config = dedent(
        """
        c = get_config()
        c.JupyterHub.authenticator_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserAuth'
        c.JupyterHub.spawner_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserSpawner'
        c.Authenticator.admin_users = set(['admin'])
        c.Authenticator.whitelist = set(['foobar', 'baz'])
        c.JupyterHub.log_level = "WARN"
        c.JupyterHub.confirm_no_ssl = True
        c.JupyterHub.port = {hub_port}
        c.JupyterHub.proxy_api_port = {proxy_port}
        c.JupyterHub.hub_port = {hubapi_port}
        """
    )

    _base_url = "http://localhost:{hub_port}"
    _base_formgrade_url = "http://localhost:{hub_port}/hub/nbgrader/course123ABC/"
    _base_notebook_url = "http://localhost:{hub_port}/user/foobar/notebooks/class_files/"

    def _write_config(self):
        super(HubAuthManager, self)._write_config()
        pth = os.path.join(self.tempdir, "jupyterhub_config.py")
        with open(pth, "w") as fh:
            fh.write(self.jupyterhub_config.format(
                tempdir=self.tempdir,
                hub_port=self.hub_port,
                hubapi_port=self.hubapi_port,
                proxy_port=self.proxy_port))

    def _start_jupyterhub(self, configproxy_auth_token='foo'):
        self.env['CONFIGPROXY_AUTH_TOKEN'] = configproxy_auth_token
        self.jupyterhub = start_subprocess(
            [sys.executable, "-m", "jupyterhub"],
            cwd=self.tempdir,
            env=self.env)

        time.sleep(self.startup_wait)

    def _start_formgrader(self, configproxy_auth_token='foo'):
        print("Getting token from jupyterhub")
        token = sp.check_output(
            [sys.executable, '-m', 'jupyterhub', 'token', 'admin'],
            cwd=self.tempdir).decode().strip()
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


class HubAuthCustomUrlManager(HubAuthManager):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NbGrader.course_id = 'course123ABC'
        c.FormgradeApp.port = {port}
        c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
        c.HubAuth.graders = ["foobar"]
        c.HubAuth.notebook_url_prefix = "class_files"
        c.HubAuth.remap_url = '/hub/grader'
        c.HubAuth.proxy_port = {proxy_port}
        c.HubAuth.hubapi_port = {hubapi_port}
        c.HubAuth.hub_port = {hub_port}
        """
    )

    _base_formgrade_url = "http://localhost:{hub_port}/hub/grader/"


class HubAuthNotebookServerUserManager(HubAuthManager):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NbGrader.course_id = 'course123ABC'
        c.FormgradeApp.port = {port}
        c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
        c.HubAuth.graders = ["foobar", "quux"]
        c.HubAuth.notebook_url_prefix = "class_files"
        c.HubAuth.notebook_server_user = 'quux'
        c.HubAuth.proxy_port = {proxy_port}
        c.HubAuth.hubapi_port = {hubapi_port}
        c.HubAuth.hub_port = {hub_port}
        """
    )

    jupyterhub_config = dedent(
        """
        c = get_config()
        c.JupyterHub.authenticator_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserAuth'
        c.JupyterHub.spawner_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserSpawner'
        c.JupyterHub.admin_access = True
        c.JupyterHub.log_level = "WARN"
        c.JupyterHub.confirm_no_ssl = True
        c.JupyterHub.port = {hub_port}
        c.JupyterHub.proxy_api_port = {proxy_port}
        c.JupyterHub.hub_port = {hubapi_port}
        c.Authenticator.admin_users = set(['admin'])
        c.Authenticator.whitelist = set(['foobar', 'baz', 'quux'])
        """
    )

    _base_notebook_url = "http://localhost:{hub_port}/user/quux/notebooks/class_files/"


class HubAuthSSLManager(HubAuthManager):

    nbgrader_config = dedent(
        """
        c = get_config()
        c.NbGrader.course_id = 'course123ABC'
        c.FormgradeApp.ip = '127.0.0.1'
        c.FormgradeApp.port = {port}
        c.FormgradeApp.authenticator_class = "nbgrader.auth.hubauth.HubAuth"
        c.HubAuth.graders = ["foobar"]
        c.HubAuth.notebook_url_prefix = "class_files"
        c.HubAuth.hub_base_url = "https://localhost:{hub_port}"
        c.HubAuth.proxy_port = {proxy_port}
        c.HubAuth.hubapi_port = {hubapi_port}
        c.HubAuth.hub_port = {hub_port}
        """
    )

    jupyterhub_config = dedent(
        """
        c = get_config()
        c.JupyterHub.authenticator_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserAuth'
        c.JupyterHub.spawner_class = 'nbgrader.tests.formgrader.fakeuser.FakeUserSpawner'
        c.Authenticator.admin_users = set(['admin'])
        c.Authenticator.whitelist = set(['foobar', 'baz'])
        c.JupyterHub.ssl_cert = '{tempdir}/jupyterhub_cert.pem'
        c.JupyterHub.ssl_key = '{tempdir}/jupyterhub_key.pem'
        c.JupyterHub.log_level = "WARN"
        c.JupyterHub.port = {hub_port}
        c.JupyterHub.proxy_api_port = {proxy_port}
        c.JupyterHub.hub_port = {hubapi_port}
        """
    )

    _base_url = "https://localhost:{hub_port}"
    _base_formgrade_url = "https://localhost:{hub_port}/hub/nbgrader/course123ABC/"
    _base_notebook_url = "https://localhost:{hub_port}/user/foobar/notebooks/class_files/"

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
