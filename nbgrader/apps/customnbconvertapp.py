import os
import glob

from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Unicode, List, Bool
from IPython.nbconvert.nbconvertapp import NbConvertApp
from IPython.nbconvert.exporters.export import exporter_map
from IPython.nbconvert.utils.exceptions import ConversionException
from IPython.nbconvert.exporters.exporter import ResourcesDict
from IPython.nbconvert.writers import FilesWriter
from IPython.core.profiledir import ProfileDir
from IPython.core.application import base_aliases, base_flags


aliases = {}
aliases.update(base_aliases)
aliases.update({
    'output': 'NbConvertApp.output_base',
    'output-dir': 'CustomNbConvertApp.output_dir'
})

flags = {}
flags.update(base_flags)
flags.update({
    'recursive': (
        {'CustomNbConvertApp': {'recursive': True}},
        "Recursively find notebook files."
    )
})

class CustomNbConvertApp(NbConvertApp):

    name = Unicode(u'nbgrader-nbconvert')
    description = Unicode(u'A custom nbconvert app')
    aliases = aliases
    flags = flags
    ipython_dir = "/tmp/nbgrader"

    recursive = Bool(False, config=True, help="Perform operations recursively through directories")
    output_dir = Unicode('', config=True, help="Output directory")

    def build_extra_config(self):
        pass

    # The classes added here determine how configuration will be documented
    classes = List()

    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        return [FilesWriter, ProfileDir]

    @catch_config_error
    def initialize(self, argv=None):
        super(CustomNbConvertApp, self).initialize(argv)
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

        matched_files = set()
        for pattern in patterns:
            # Use glob to find matching filenames
            globbed_files = glob.glob(pattern)
            if not globbed_files:
                self.log.warn("pattern %r matched no files", pattern)

            # Go through the globbed files and add them, possibly
            # recursively if specified
            for globbed in globbed_files:
                if os.path.isdir(globbed) and self.recursive:
                    for dirpath, dirnames, filenames in os.walk(globbed):
                        for filename in filenames:
                            if os.path.splitext(filename)[1] == '.ipynb':
                                matched_files.add((dirpath, filename))

                        # skip checkpoint directories
                        if '.ipynb_checkpoints' in dirnames:
                            dirnames.remove('.ipynb_checkpoints')

                elif not os.path.isdir(globbed):
                    matched_files.add(os.path.split(globbed))

        self.notebooks = sorted(matched_files)

        if self.recursive:
            self.prefix = os.path.commonprefix(zip(*self.notebooks)[0])
            while not os.path.isdir(self.prefix):
                self.prefix = os.path.split(self.prefix)[0]
            self.log.info("Directory tree prefix: {}".format(self.prefix))
        else:
            self.prefix = '.'

    def convert_notebooks(self):
        """
        Convert the notebooks in the self.notebook traitlet
        """
        # Export each notebook
        conversion_success = 0

        if self.output_base != '' and len(self.notebooks) > 1:
            self.log.error(
                """UsageError: --output flag or `NbConvertApp.output_base` config
                option cannot be used when converting multiple
                notebooks. Did you mean to use --output-dir?""")
            self.exit(1)

        exporter = exporter_map[self.export_format](config=self.config)
        cwd = os.getcwd()

        for notebook_path, notebook_filename in self.notebooks:
            os.chdir(cwd)
            if notebook_path != '':
                self.log.info("Changing to directory: %s", notebook_path)
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
            # TODO: end

            self.log.info("Support files will be in %s", os.path.join(
                resources['output_files_dir'], ''))

            if self.recursive:
                prefix = os.path.relpath(notebook_path, self.prefix)
                self.writer.build_directory = os.path.join(self.output_dir, prefix)
            else:
                if self.output_dir == '':
                    self.writer.build_directory = '.'
                else:
                    self.writer.build_director = self.output_dir

            # Try to export
            try:
                output, resources = exporter.from_filename(notebook_filename, resources=resources)
            except ConversionException:
                self.log.error(
                    "Error while converting '%s'",
                    notebook_filename, exc_info=True)
                self.exit(1)

            self.log.info("Writing output to directory: {}".format(
                os.path.relpath(self.writer.build_directory, cwd)))
            self.writer.write(output, resources, notebook_name=notebook_name)

        # Post-process if post processor has been defined.
        if hasattr(self, 'postprocessor') and self.postprocessor:
            os.chdir(cwd)
            self.postprocessor(cwd)
        conversion_success += 1
