from .base import BaseAuthenticator


class JupyterHubAuthenticator(BaseAuthenticator):

    def get_student_courses(self, student_id):
        return []

    def has_access(self, student_id, course_id):
        return True

    def add_student_to_course(self):
        pass

    def remove_student_from_course(self):
        pass
