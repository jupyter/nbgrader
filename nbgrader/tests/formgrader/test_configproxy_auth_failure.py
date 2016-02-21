import pytest

from .manager import HubAuthManager
from .conftest import jupyterhub


@jupyterhub
def test_configproxy_auth_success(gradebook, tempdir):
    """Can the formgrader be started with the correct auth token?"""

    man = HubAuthManager(tempdir)
    man._write_config()

    man._start_jupyterhub(configproxy_auth_token='foo')
    man._start_formgrader(configproxy_auth_token='foo')

    assert man.jupyterhub.poll() is None
    assert man.formgrader.poll() is None

    man._stop_formgrader()
    man._stop_jupyterhub()

    assert man.formgrader.poll() == 0
    assert man.jupyterhub.poll() == 0


@jupyterhub
def test_configproxy_auth_failure(gradebook, tempdir):
    """Can the formgrader not be started when the auth token is incorrect?"""

    man = HubAuthManager(tempdir)
    man._write_config()

    man._start_jupyterhub(configproxy_auth_token='foo')
    man._start_formgrader(configproxy_auth_token='bar')

    assert man.jupyterhub.poll() is None
    assert man.formgrader.poll() == 1

    man._stop_jupyterhub()

    assert man.jupyterhub.poll() == 0
