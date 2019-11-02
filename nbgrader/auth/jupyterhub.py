import os
import requests

from .base import BaseAuthPlugin


class JupyterhubEnvironmentError(Exception):
    pass


class JupyterhubApiError(Exception):
    pass


def get_jupyterhub_user():
    if os.getenv('JUPYTERHUB_USER'):
        return os.environ['JUPYTERHUB_USER']
    else:
        raise JupyterhubEnvironmentError("JUPYTERHUB_USER env is required to run the exchange features of nbgrader.")


def get_jupyterhub_api_url():
    return os.environ.get('JUPYTERHUB_API_URL') or 'http://127.0.0.1:8081/hub/api'


def get_jupyterhub_authorization():
    if os.getenv('JUPYTERHUB_API_TOKEN'):
        api_token = os.environ['JUPYTERHUB_API_TOKEN']
    else:
        raise JupyterhubEnvironmentError("JUPYTERHUB_API_TOKEN env is required to run the exchange features of nbgrader.")
    return {
        'Authorization': 'token %s' % api_token
    }


def _query_jupyterhub_api(method, api_path, post_data=None):
    """Query Jupyterhub api

    Detects Jupyterhub environment variables and makes a call to the Hub API

    Parameters
    ----------
    method : string
        HTTP method, e.g. GET or POST
    api_path : string
        relative path, for example /users/
    post_data : dict
        JSON arguments for the API call

    Returns
    -------
    response : dict
        JSON response converted to dictionary

    """
    hub_api_url = get_jupyterhub_api_url()
    user = get_jupyterhub_user()
    auth_header = get_jupyterhub_authorization()
    api_path = api_path.format(authenticated_user=user)
    req = requests.request(
        url=hub_api_url + api_path,
        method=method,
        headers=auth_header,
        json=post_data,
    )
    if not req.ok:
        raise JupyterhubApiError("JupyterhubAPI returned a status code of: " + str(req.status_code) + " for api_path: " + api_path)

    return req.json()


class JupyterHubAuthPlugin(BaseAuthPlugin):

    def get_student_courses(self, student_id):
        if student_id == "*":
            student_id = "{authenticated_user}"
        response = None
        try:
            response = _query_jupyterhub_api('GET', '/users/%s' % student_id)
        except JupyterhubEnvironmentError: # Should only go here if we are not running on Jupyterhub.
            self.log.info('Not running on Jupyterhub, not able to GET Jupyterhub user')
            raise
        except JupyterhubApiError: # Should only go here if the api_token is invalid.
            self.log.error("Error: Not able to get Jupyterhub user: " + student_id)
            self.log.error("Make sure you start your service with a valid admin_user 'api_token' in your Jupyterhub config")
            raise
        courses = set()
        for group in response['groups']:
            if group.startswith('nbgrader-') or group.startswith('formgrade-'):
                course = group.split('-', 1)[1]
                if course:
                    courses.add(course)
        return list(courses)

    def add_student_to_course(self, student_id, course_id):
        if not course_id:
            self.log.error(
                "Could not add student to course because the course_id has not "
                "been provided. Has it been set in the nbgrader_config.py?")
            return

        try:
            group_name = "nbgrader-{}".format(course_id)
            jup_groups = _query_jupyterhub_api(
                method="GET",
                api_path="/groups",
            )
            if group_name not in [x['name'] for x in jup_groups]:
                # This could result in a bad request(JupyterhubApiError) if
                # there is already a group so first we check above if there is a
                # group
                _query_jupyterhub_api(
                    method="POST",
                    api_path="/groups/{name}".format(name=group_name),
                )
                self.log.info("Jupyterhub group: {group_name} created.".format(
                    group_name=group_name))

            _query_jupyterhub_api(
                method="POST",
                api_path="/groups/{name}/users".format(name=group_name),
                post_data={"users": [student_id]}
            )
            # Saying student could be already here is because the post request
            # returns 200 even if the student_id was already in the group
            self.log.info(
                "Student {student} added or was already in the Jupyterhub group: {group_name}".format(
                    student=student_id,
                    group_name=group_name))

        except JupyterhubApiError as e:
            # We assume user might be using Jupyterhub but something is not working
            err_msg = "Student {student} NOT added to the Jupyterhub group {group_name}: ".format(
                student=student_id,
                group_name=group_name
            )
            self.log.error(err_msg + str(e))
            self.log.error("Make sure you set a valid admin_user 'api_token' in your config file before starting the service")

    def remove_student_from_course(self, student_id, course_id):
        if not course_id:
            self.log.error(
                "Could not remove student from course because the course_id has "
                "not been provided. Has it been set in the nbgrader_config.py?")
            return

        try:
            group_name = "nbgrader-{}".format(course_id)
            _query_jupyterhub_api(
                method="DELETE",
                api_path="/groups/{name}/users".format(name=group_name),
                post_data={"users": [student_id]}
            )
            self.log.info(
                "Student {student} was removed or was already not in the Jupyterhub group {group_name}".format(
                    student=student_id, group_name=group_name))

        except JupyterhubApiError as e:
            self.log.error(
                "Student {student} was NOT removed from the Jupyterhub group {group_name}:".format(
                    student=student_id, group_name=group_name), str(e))
            self.log.error(
                "Make sure you start your service with a valid admin_user 'api_token' in your Jupyterhub config")
