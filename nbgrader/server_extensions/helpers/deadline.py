import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ... import utils


class DeadlineManager:
    def __init__(self, config, logger):
        self.config = config
        self.log = logger
    
    def fetch_deadlines(self, assignments):
        """Fetch the deadline for the given course id and assignments."""

        dir_name = os.path.join(self.config.Exchange.root, self.config.CourseDirectory.course_id)
        file_path = os.path.join(dir_name, self.config.Exchange.deadline_file)
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
        with open(file_path, "w") as fh:
            for assignment, deadline in deadlines.items():
                fh.write(f"{assignment}/{deadline}\n")
        
        if self.config.CourseDirectory.groupshared:
            st_mode = os.stat(file_path).st_mode
            if st_mode & 0o660 != 0o660:
                try:
                    os.chmod(file_path, (st_mode | 0o660) & 0o777)
                except PermissionError:
                    self.log.warning("Could not update permissions of %s to make it groupshared", file_path)
                
    
    def _format_deadline(self, deadline):
        """Format the deadline."""
        tz = "UTC"  # Default timezone
        if self.config.Exchange.timezone:
            tz = self.config.Exchange.timezone
        try:
             tzinfo = ZoneInfo(tz)
        except ZoneInfoNotFoundError:
            self.log.error("Invalid deadline format: {}".format(deadline))
            tzinfo = ZoneInfo("UTC")
            
        return utils.parse_utc(deadline) \
            .replace(tzinfo=ZoneInfo("UTC")) \
            .astimezone(tzinfo) \
            .strftime("%Y-%m-%d %H:%M:%S %Z")

    def _read_deadlines(self, file_path):
        """Read the deadlines from the deadlines file."""

        try:
            with open(file_path, "r") as fh:
                lines = fh.readlines()       
        except FileNotFoundError:
            self.log.warning("No deadlines file found at {}".format(file_path))
            return {}
        return self._parse_deadlines(lines)
        
    def _parse_deadlines(self, lines):
        """Parse the deadlines from the lines."""
        deadlines = {}
        for line in lines:
            parts = line.split("/")
            if len(parts) != 2:
                self.log.warning("Invalid deadline line: {}".format(line))
            assignment, deadline = parts
            deadlines[assignment.strip()] = deadline.strip()
        return deadlines
