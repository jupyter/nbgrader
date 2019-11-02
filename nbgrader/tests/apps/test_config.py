from traitlets.config import Config
from ...coursedir import CourseDirectory
from .base import BaseTestApp
from .conftest import notwindows

class TestCourseDirectory(BaseTestApp):

    @notwindows
    def test_format_path(self):
        config = Config()
        config.Exchange.course_id = "abc101"
        config.CourseDirectory.root = "/root"
        coursedir = CourseDirectory(config=config)
        # Test the support for both absolute paths and paths relative to the root directory
        # See #1222
        assert coursedir.format_path("submitted", "alice", "HW1") == "/root/submitted/alice/HW1"
        assert coursedir.format_path("/bar/submitted", "alice", "HW1") == "/bar/submitted/alice/HW1"
