import json
import os
from zoneinfo import ZoneInfo

from ... import utils


class DeadlineManager:
    def __init__(self, exchange_root, coursedir, logger):
        self.exchange_root = exchange_root
        self.coursedir = coursedir
        self.log = logger
    
    def fetch_deadlines(self, assignments):
        """Fetch the deadline for the given course id and assignments."""
        if not self.exchange_root:  # Non-FS based exchange
            return assignments
        
        dir_name = os.path.join(self.exchange_root, self.coursedir.course_id)
        file_path = os.path.join(dir_name, self.coursedir.deadline_file)
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
        if not self.exchange_root:  # Non-FS based exchange
            return
        
        deadline = self._format_deadline(deadline)
        
        dir_name = os.path.join(self.exchange_root, self.coursedir.course_id)
        file_path = os.path.join(dir_name, self.coursedir.deadline_file)
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
        except:
            self.log.error("An unexpected error occurred while writing deadlines")
            return
        
        access_mode = 0o664 if self.coursedir.groupshared else 0o644
        st_mode = os.stat(file_path).st_mode
        if st_mode & access_mode != access_mode:
            try:
                os.chmod(file_path, (st_mode | access_mode) & 0o777)
            except PermissionError:
                self.log.warning("Could not update permissions of %s", file_path)
            except:
                self.log.error("An unexpected error occurred while updating permissions of %s", file_path)
    
    def _format_deadline(self, deadline):
        """Format the deadline."""
        
        return utils.parse_utc(deadline) \
            .replace(tzinfo=ZoneInfo("UTC")) \
            .isoformat()

    def _read_deadlines(self, file_path):
        """Read the deadlines from the deadlines file."""

        try:
            entries = json.load(open(file_path, "r"))
        except (FileNotFoundError, PermissionError):
            self.log.warning("No deadlines file found or accessible at {}".format(file_path))
            return {}
        except json.JSONDecodeError:
            self.log.warning("Invalid JSON in deadlines file at {}".format(file_path))
            return {}
        except:
            self.log.error("An unexpected error occurred while loading deadlines")
            return {}
        return entries
