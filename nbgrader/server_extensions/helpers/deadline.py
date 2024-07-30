import json
import os
from zoneinfo import ZoneInfo

from ... import utils


class DeadlineManager:
    def __init__(self, config, logger):
        self.config = config
        self.log = logger
    
    def fetch_deadlines(self, assignments):
        """Fetch the deadline for the given course id and assignments."""

        dir_name = os.path.join(self.config.Exchange.root, self.config.CourseDirectory.course_id)
        file_path = os.path.join(dir_name, self.config.Exchange.deadline_file)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self.log.warning("No deadlines file found at {}".format(file_path))
            return assignments

        deadlines = self._read_deadlines(file_path)
        for assignment in assignments:
            if assignment["assignment_id"] in deadlines:
                assignment["due_date"] = deadlines[assignment["assignment_id"]]
        return assignments
   
    def update_or_add_deadline(self, assignment_id, deadline):
        """Add a deadline in the deadlines file or update it if it exists."""
        deadline = self._format_deadline(deadline)
        
        dir_name = os.path.join(self.config.Exchange.root, self.config.CourseDirectory.course_id)
        file_path = os.path.join(dir_name, self.config.Exchange.deadline_file)
        deadlines = self._read_deadlines(file_path)
        deadlines[assignment_id] = deadline
        
        self._write_deadlines(file_path, deadlines)
    
    def _write_deadlines(self, file_path, deadlines):
        """Write the deadlines to the deadlines file and sets access permissions."""
        try:
            json.dump(deadlines, open(file_path, "w"))
        except (FileNotFoundError, PermissionError) as e:
            self.log.error("The path to file does not exist or not permitted: %s", e)
            return
        except IsADirectoryError:
            self.log.error("The path to file is a directory: %s", file_path)
            return
        except TypeError:
            self.log.error("Invalid data type to write in file: %s", deadlines)
            return
        
        access_mode = 0o664 if self.config.CourseDirectory.groupshared else 0o644
        st_mode = os.stat(file_path).st_mode
        if st_mode & access_mode != access_mode:
            try:
                os.chmod(file_path, (st_mode | access_mode) & 0o777)
            except PermissionError:
                self.log.warning("Could not update permissions of %s", file_path)
    
    def _format_deadline(self, deadline):
        """Format the deadline."""
        
        return utils.parse_utc(deadline) \
            .replace(tzinfo=ZoneInfo("UTC")) \
            .isoformat()

    def _read_deadlines(self, file_path):
        """Read the deadlines from the deadlines file."""

        try:
            entries = json.load(open(file_path, "r"))
        except FileNotFoundError:
            self.log.warning("No deadlines file found at {}".format(file_path))
            return {}
        except json.JSONDecodeError:
            self.log.warning("Invalid JSON in deadlines file at {}".format(file_path))
            return {}
        return entries
