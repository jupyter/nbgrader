import os

from jupyterhub.auth import LocalAuthenticator
from jupyterhub.spawner import LocalProcessSpawner
from tornado import gen

class FakeUserAuth(LocalAuthenticator):
    """Authenticate fake users"""

    @gen.coroutine
    def authenticate(self, handler, data):
        """If the user is on the whitelist, authenticate regardless of password.
        If not, then don't authenticate.

        """
        username = data['username']
        if not self.check_whitelist(username):
            return
        return username

    @staticmethod
    def system_user_exists(user):
        return True


class FakeUserSpawner(LocalProcessSpawner):

    def user_env(self, env):
        env['USER'] = self.user.name
        env['HOME'] = os.getcwd()
        env['SHELL'] = '/bin/bash'
        return env

    def make_preexec_fn(self, name):
        home = os.getcwd()
        def preexec():
            # start in the cwd
            os.chdir(home)
        return preexec
