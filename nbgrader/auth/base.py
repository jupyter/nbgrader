from traitlets.config import LoggingConfigurable


class BaseAuthenticator(LoggingConfigurable):

    def get_student_courses(self, student_id):
        """Gets the list of courses that the student is enrolled in.

        Arguments
        ---------
        student_id: string
            The unique id of the student.

        Returns
        -------
        A list of unique course ids, or None. If None is returned this means
        that the student has access to any course that might exist. Otherwise
        the student is only allowed access to the specific courses returned in
        the list.

        """
        raise NotImplementedError

    def has_access(self, student_id, course_id):
        """Checks whether a student has access to a particular course.

        Arguments
        ---------
        student_id: string
            The unique id of the student.
        course_id: string
            The unique id of the course.

        Returns
        -------
        A boolean indicating whether the student has access.

        """
        courses = self.get_student_courses(student_id)
        if courses is None:
            return True
        return course_id in courses

    def add_student_to_course(self, student_id, course_id):
        """Grants a student access to a given course.

        Arguments
        ---------
        student_id: string
            The unique id of the student.
        course_id: string
            The unique id of the course.

        """
        raise NotImplementedError

    def remove_student_from_course(self, student_id, course_id):
        """Removes a student's access to a given course.

        Arguments
        ---------
        student_id: string
            The unique id of the student.
        course_id: string
            The unique id of the course.

        """
        raise NotImplementedError
