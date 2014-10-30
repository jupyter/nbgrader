import os
import sys
import glob

from IPython.config.loader import Config
from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Unicode
from IPython.nbconvert.nbconvertapp import NbConvertApp
from IPython.nbconvert.nbconvertapp import nbconvert_aliases, nbconvert_flags
from IPython.nbconvert.exporters.export import exporter_map
from IPython.nbconvert.utils.exceptions import ConversionException
from IPython.nbconvert.exporters.exporter import ResourcesDict


aliases = {}
aliases.update(nbconvert_aliases)
aliases.update({
      'student-id': 'CustomNbConvertApp.student_id'
})

flags = {}
flags.update(nbconvert_flags)
flags.update({
})


class CustomNbConvertApp(NbConvertApp):
    
    name = Unicode(u'nbgrader-nbconvert')
    description = Unicode(u'A custom nbconvert app')
    aliases = aliases
    flags = flags

    student_id = Unicode(u'', config=True)

    def build_extra_config(self):
        pass

    @catch_config_error
    def initialize(self, argv=None):
        super(CustomNbConvertApp,self).initialize(argv)
        self.stage_default_config_file()
        self.build_extra_config()

    def init_notebooks(self):
        """Construct the list of notebooks.
        If notebooks are passed on the command-line,
        they override notebooks specified in config files.
        Glob each notebook to replace notebook patterns with filenames.
        """

        # Specifying notebooks on the command-line overrides (rather than adds)
        # the notebook list
        if self.extra_args:
            patterns = self.extra_args
        else:
            patterns = self.notebooks

        # Use glob to replace all the notebook patterns with filenames.
        filenames = []
        for pattern in patterns:
            
            # Use glob to find matching filenames.  Allow the user to convert 
            # notebooks without having to type the extension.
            globbed_files = glob.glob(pattern)
            globbed_files.extend(glob.glob(pattern + '.ipynb'))
            if not globbed_files:
                self.log.warn("pattern %r matched no files", pattern)

            for filename in globbed_files:
                if not filename in filenames:
                    filename = os.path.abspath(filename)
                    filenames.append(os.path.split(filename))
        self.notebooks = filenames

    def convert_notebooks(self):
        """
        Convert the notebooks in the self.notebook traitlet
        """
        # Export each notebook
        conversion_success = 0

        if self.output_base != '' and len(self.notebooks) > 1:
            self.log.error(
            """UsageError: --output flag or `NbConvertApp.output_base` config option
            cannot be used when converting multiple notebooks.
            """)
            self.exit(1)

        exporter = exporter_map[self.export_format](config=self.config)
        cwd = os.getcwd()

        for notebook_path, notebook_filename in self.notebooks:
            if os.getcwd() != notebook_path:
                self.log.info("Changing to directory %s", notebook_path)
                os.chdir(notebook_path)
            self.log.info("Converting notebook %s to %s", notebook_filename, self.export_format)

            # Get a unique key for the notebook and set it in the resources object.
            basename = os.path.basename(notebook_filename)
            notebook_name = basename[:basename.rfind('.')]
            if self.output_base:
                # strip duplicate extension from output_base, to avoid Basname.ext.ext
                if getattr(exporter, 'file_extension', False):
                    base, ext = os.path.splitext(self.output_base)
                    if ext == '.' + exporter.file_extension:
                        self.output_base = base
                notebook_name = self.output_base
            resources = {}
            resources['profile_dir'] = self.profile_dir.location
            resources['unique_key'] = notebook_name
            resources['output_files_dir'] = '%s_files' % notebook_name

            # TODO: refactor these custom resources hacks - put path setting in Exporter
            resources['metadata'] = ResourcesDict()
            resources['metadata']['path'] = notebook_path
            resources['nbgrader'] = ResourcesDict()
            # Always set student_id, might be empty
            resources['nbgrader']['student_id'] = self.student_id
            # TODO: end

            self.log.info("Support files will be in %s", os.path.join(resources['output_files_dir'], ''))

            # Try to export
            try:
                output, resources = exporter.from_filename(notebook_filename, resources=resources)
            except ConversionException as e:
                self.log.error("Error while converting '%s'", notebook_filename,
                      exc_info=True)
                self.exit(1)
            else:
                write_results = self.writer.write(output, resources, notebook_name=notebook_name)

        # Post-process if post processor has been defined.
        if hasattr(self, 'postprocessor') and self.postprocessor:
            self.postprocessor(cwd)
        conversion_success += 1
