from .base import BaseAuthenticator


class NoAuthentication(BaseAuthenticator):

    def get_student_courses(self, student_id):
        # None means that the student has access to any course that might exist
        # on the system.
        return None

    def has_access(self, student_id, course_id):
        return True

    def add_student_to_course(self):
        # Nothing to do, we don't keep track of which students are in which
        # courses in the default setting.
        pass

    def remove_student_from_course(self):
        # Nothing to do, we don't keep track of which students are in which
        # courses in the default setting.
        pass
