import os
import pytest
import requests_mock
from traitlets.config import Config

from ..auth import Authenticator, JupyterHubAuthPlugin
from ..auth.jupyterhub import JupyterhubEnvironmentError, JupyterhubApiError


@pytest.fixture
def env(request):
    old_env = os.environ.copy()

    def fin():
        os.environ = old_env
    request.addfinalizer(fin)

    return os.environ


@pytest.fixture
def jupyterhub_auth():
    config = Config()
    config.Authenticator.plugin_class = JupyterHubAuthPlugin
    auth = Authenticator(config=config)
    return auth


def _mock_api_call(method, path, status_code=None, json=None):
    hub_api_url = 'http://127.0.0.1:8081/hub/api'
    url = hub_api_url + path

    def _set_json(request, context):
        assert request.headers['Authorization'] == 'token abcd1234'
        context.status_code = 200
        return json or []

    if status_code is None:
        method(url, json=_set_json)
    else:
        method(url, status_code=status_code)


def test_default_authenticator():
    auth = Authenticator()
    assert auth.get_student_courses("foo") is None
    assert auth.has_access("foo", "course123")

    # smoke tests, these should just do nothing
    auth.add_student_to_course("foo", "course123")
    auth.remove_student_from_course("bar", "course123")


def test_jupyterhub_get_student_courses(env, jupyterhub_auth):
    # this will fail, because the user hasn't been set
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = ''
    with pytest.raises(JupyterhubEnvironmentError):
        jupyterhub_auth.get_student_courses('foo')

    # this will fail, because the api token hasn't been set
    env['JUPYTERHUB_API_TOKEN'] = ''
    env['JUPYTERHUB_USER'] = 'foo'
    with pytest.raises(JupyterhubEnvironmentError):
        jupyterhub_auth.get_student_courses('foo')

    # should fail, because the server returns a forbidden response
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = 'foo'
    with requests_mock.Mocker() as m:
        _mock_api_call(m.get, '/users/foo', status_code=403)
        with pytest.raises(JupyterhubApiError):
            jupyterhub_auth.get_student_courses('foo')

    # should succeed, but give no courses, because the group name is invalid
    with requests_mock.Mocker() as m:
        _mock_api_call(m.get, '/users/foo', json={'groups': ['nbgrader-']})
        assert jupyterhub_auth.get_student_courses('foo') == []

        _mock_api_call(m.get, '/users/foo', json={'groups': ['course101']})
        assert jupyterhub_auth.get_student_courses('foo') == []

        _mock_api_call(
            m.get, '/users/foo', json={'groups': ['nbgrader-course123']})
        assert jupyterhub_auth.get_student_courses('foo') == ['course123']

    # should succeed
    with requests_mock.Mocker() as m:
        _mock_api_call(
            m.get, '/users/foo', json={'groups': ['nbgrader-course123']})
        assert jupyterhub_auth.get_student_courses('*') == ['course123']


def test_jupyterhub_has_access(env, jupyterhub_auth):
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = 'foo'
    with requests_mock.Mocker() as m:
        _mock_api_call(
            m.get, '/users/foo', json={'groups': ['nbgrader-course123']})
        assert jupyterhub_auth.has_access('foo', 'course123')
        assert not jupyterhub_auth.has_access('foo', 'courseABC')


def test_jupyterhub_add_student_to_course_no_token(jupyterhub_auth):
    # this will fail, because the api token hasn't been set
    with pytest.raises(JupyterhubEnvironmentError):
        jupyterhub_auth.add_student_to_course('foo', 'course123')


def test_jupyterhub_add_student_to_course_no_user(env, jupyterhub_auth):
    # should still fail, because the user hasn't been set
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    with pytest.raises(JupyterhubEnvironmentError):
        jupyterhub_auth.add_student_to_course('foo', 'course123')


def test_jupyterhub_add_student_to_course_forbidden(env, jupyterhub_auth, caplog):
    # test case where something goes wrong
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = 'foo'
    with requests_mock.Mocker() as m:
        _mock_api_call(m.get, '/groups', status_code=403)
        jupyterhub_auth.add_student_to_course('foo', 'course123')
        assert 'ERROR' in [rec.levelname for rec in caplog.records]


def test_jupyterhub_add_student_to_course_no_courseid(env, jupyterhub_auth, caplog):
    # test case where something goes wrong
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = 'foo'
    with requests_mock.Mocker() as m:
        _mock_api_call(m.get, '/groups', status_code=403)
        jupyterhub_auth.add_student_to_course('foo', None)
        assert 'ERROR' in [rec.levelname for rec in caplog.records]


def test_jupyterhub_add_student_to_course_success(env, jupyterhub_auth, caplog):
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = 'foo'
    with requests_mock.Mocker() as m:
        _mock_api_call(m.get, '/groups', json=[])
        _mock_api_call(m.post, '/groups/nbgrader-course123')
        _mock_api_call(m.post, '/groups/nbgrader-course123/users')
        jupyterhub_auth.add_student_to_course('foo', 'course123')
        assert 'ERROR' not in [rec.levelname for rec in caplog.records]

        # Check that it also works if the group already exists
        _mock_api_call(m.get, '/groups', json=[{'name': 'nbgrader-course123'}])
        _mock_api_call(m.post, '/groups/nbgrader-course123/users')
        jupyterhub_auth.add_student_to_course('foo', 'course123')
        assert 'ERROR' not in [rec.levelname for rec in caplog.records]


def test_jupyterhub_remove_student_from_course_no_token(jupyterhub_auth):
    # this will fail, because the api token hasn't been set
    with pytest.raises(JupyterhubEnvironmentError):
        jupyterhub_auth.remove_student_from_course('foo', 'course123')


def test_jupyterhub_remove_student_from_course_no_user(env, jupyterhub_auth):
    # should still fail, because the user hasn't been set
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    with pytest.raises(JupyterhubEnvironmentError):
        jupyterhub_auth.remove_student_from_course('foo', 'course123')


def test_jupyterhub_remove_student_from_course_forbidden(env, jupyterhub_auth, caplog):
    # test case where something goes wrong
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = 'foo'
    with requests_mock.Mocker() as m:
        _mock_api_call(m.delete, '/groups/nbgrader-course123/users', status_code=403)
        jupyterhub_auth.remove_student_from_course('foo', 'course123')
        assert 'ERROR' in [rec.levelname for rec in caplog.records]


def test_jupyterhub_remove_student_from_course_no_courseid(env, jupyterhub_auth, caplog):
    # test case where something goes wrong
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = 'foo'
    with requests_mock.Mocker() as m:
        _mock_api_call(m.delete, '/groups/nbgrader-course123/users')
        jupyterhub_auth.remove_student_from_course('foo', None)
        assert 'ERROR' in [rec.levelname for rec in caplog.records]


def test_jupyterhub_remove_student_from_course_success(env, jupyterhub_auth, caplog):
    env['JUPYTERHUB_API_TOKEN'] = 'abcd1234'
    env['JUPYTERHUB_USER'] = 'foo'
    with requests_mock.Mocker() as m:
        _mock_api_call(m.delete, '/groups/nbgrader-course123/users')
        jupyterhub_auth.remove_student_from_course('foo', 'course123')
        assert 'ERROR' not in [rec.levelname for rec in caplog.records]
