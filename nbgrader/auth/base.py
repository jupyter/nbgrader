from traitlets import Instance, Type
from traitlets.config import LoggingConfigurable
from typing import Any, Optional


class BaseAuthPlugin(LoggingConfigurable):

    def get_student_courses(self, student_id: str) -> Optional[list]:  # pragma: no cover
        """Gets the list of courses that the student is enrolled in.

        Arguments
        ---------
        student_id:
            The unique id of the student.

        Returns
        -------
        A list of unique course ids, or None. If None is returned this means
        that the student has access to any course that might exist. Otherwise
        the student is only allowed access to the specific courses returned in
        the list.

        """
        raise NotImplementedError

    def add_student_to_course(self, student_id: str, course_id: str) -> None:  # pragma: no cover
        """Grants a student access to a given course.

        Arguments
        ---------
        student_id:
            The unique id of the student.
        course_id:
            The unique id of the course.

        """
        raise NotImplementedError

    def remove_student_from_course(self, student_id: str, course_id: str) -> None:  # pragma: no cover
        """Removes a student's access to a given course.

        Arguments
        ---------
        student_id:
            The unique id of the student.
        course_id:
            The unique id of the course.

        """
        raise NotImplementedError


class NoAuthPlugin(BaseAuthPlugin):

    def get_student_courses(self, student_id: str) -> Optional[list]:
        # None means that the student has access to any course that might exist
        # on the system.
        return None

    def add_student_to_course(self, student_id: str, course_id: str) -> None:
        # Nothing to do, we don't keep track of which students are in which
        # courses in the default setting.
        pass

    def remove_student_from_course(self, student_id: str, course_id: str) -> None:
        # Nothing to do, we don't keep track of which students are in which
        # courses in the default setting.
        pass


class Authenticator(LoggingConfigurable):

    plugin_class = Type(
        NoAuthPlugin,
        klass=BaseAuthPlugin,
        help="A plugin for different authentication methods."
    ).tag(config=True)

    plugin = Instance(BaseAuthPlugin).tag(config=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.log.debug("Using authenticator: %s", self.plugin_class.__name__)
        self.plugin = self.plugin_class(parent=self)

    def get_student_courses(self, student_id: str) -> Optional[list]:
        """Gets the list of courses that the student is enrolled in.

        Arguments
        ---------
        student_id:
            The unique id of the student.

        Returns
        -------
        A list of unique course ids, or None. If None is returned this means
        that the student has access to any course that might exist. Otherwise
        the student is only allowed access to the specific courses returned in
        the list.

        """
        return self.plugin.get_student_courses(student_id)

    def has_access(self, student_id: str, course_id: str) -> bool:
        """Checks whether a student has access to a particular course.

        Arguments
        ---------
        student_id:
            The unique id of the student.
        course_id:
            The unique id of the course.

        Returns
        -------
        A boolean indicating whether the student has access.

        """
        courses = self.get_student_courses(student_id)
        if courses is None:
            return True
        return course_id in courses

    def add_student_to_course(self, student_id: str, course_id: str) -> None:
        """Grants a student access to a given course.

        Arguments
        ---------
        student_id:
            The unique id of the student.
        course_id:
            The unique id of the course.

        """
        self.plugin.add_student_to_course(student_id, course_id)

    def remove_student_from_course(self, student_id: str, course_id: str) -> None:
        """Removes a student's access to a given course.

        Arguments
        ---------
        student_id:
            The unique id of the student.
        course_id:
            The unique id of the course.

        """
        self.plugin.remove_student_from_course(student_id, course_id)
