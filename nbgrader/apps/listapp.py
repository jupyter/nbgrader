import os
import glob
import shutil

from IPython.utils.traitlets import Bool

from nbgrader.apps.baseapp import TransferApp, transfer_aliases, transfer_flags


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
    'inbound': (
        {'ListApp' : {'inbound': True}},
        "List inbound files rather than outbound."
    ),
    'remove': (
        {'ListApp' : {'remove': True}},
        "Remove an assignment from the exchange."
    ),
})

class ListApp(TransferApp):

    name = u'nbgrader-list'
    description = u'List assignments in the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        List assignments in the nbgrader exchange. For the usage of instructors
        and students.
        
        Students
        ========
        
        To list assignments for a course, you must first know the `course_id` for
        your course. If you don't know it, ask your instructor.
        
        To list the released assignments for the course `phys101`:
        
            nbgrader list phys101
        
        Instructors
        ===========
        
        To list outbound (released) or inbound (submitted) assignments for a course,
        you must configure the `course_id` in your config file or the command line.
        
        To see all of the released assignments, run
        
            nbgrader list  # course_id in the config file
        
        or
        
            nbgrader list phys101  # course_id provided
            
        To see the inbound (submitted) assignments:
        
            nbgrader list --inbound phys101
        
        You can use the `--student` and `--assignment` options to filter the list
        by student or assignment:
        
            nbgrader list --inbound --student=student1 --assignment=assignment1 phys101
        
        If a student has submitted an assignment multiple times, the `list` command
        will show all submissions with their timestamps.
        
        The `list` command can optionally remove listed assignments by providing the
        `--remove` flag:
        
            nbgrader list --inbound --remove --student=student1 phys101
        """

    inbound = Bool(False, config=True, help="List inbound files rather than outbound.")
    
    remove = Bool(False, config=True, help="Remove, rather than list files.")
    
    def init_args(self):
        if len(self.extra_args) == 0:
            pass
        elif len(self.extra_args) == 1:
            self.course_id = self.extra_args[0]
        else:
            self.fail("Invalid number of argument, call as `nbgrader list COURSE`.")

    def init_src(self):
        pass
    
    def init_dest(self):
        self.course_path = os.path.join(self.exchange_directory, self.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        if self.inbound:
            student_id = self.student_id if self.student_id else '*'
            assignment_id = self.assignment_id if self.assignment_id else '*'
            pattern = os.path.join(self.inbound_path, '{}+{}+*'.format(student_id, assignment_id))
        else:
            pattern = os.path.join(self.outbound_path, '*')
        self.assignments = glob.glob(pattern)

    def copy_files(self):
        pass
    
    def list_files(self):
        """List files."""
        if self.inbound:
            self.log.info("Submitted assignments:")
            for path in self.assignments:
                username, assignment, timestamp = os.path.split(path)[1].rsplit('+',2)
                self.log.info("{} {} {} {}".format(
                    self.course_id, username, assignment, timestamp
                ))
        else:
            self.log.info("Released assignments:")
            for path in self.assignments:
                self.log.info("{} {}".format(self.course_id, os.path.split(path)[1]))
    
    def remove_files(self):
        """List and remove files."""
        if self.inbound:
            self.log.info("Removing submitted assignments:")
            for path in self.assignments:
                username, assignment, timestamp = os.path.split(path)[1].rsplit('+',2)
                self.log.info("{} {} {} {}".format(
                    self.course_id, username, assignment, timestamp
                ))
                shutil.rmtree(path)
        else:
            self.log.info("Removing released assignments:")
            for path in self.assignments:
                self.log.info("{} {}".format(self.course_id, os.path.split(path)[1]))
                shutil.rmtree(path)

    def start(self):
        super(ListApp, self).start() 
        if self.remove:
            self.remove_files()
        else:
            self.list_files()


