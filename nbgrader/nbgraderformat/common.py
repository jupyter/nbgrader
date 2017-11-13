import json
import os
import jsonschema

from jsonschema import ValidationError
from traitlets.config import LoggingConfigurable
from . import SCHEMA_VERSION


root = os.path.dirname(__file__)


class SchemaMismatchError(Exception):

    def __init__(self, message, actual_version, expected_version):
        super(SchemaMismatchError, self).__init__(message)
        self.actual_version = actual_version
        self.expected_version = expected_version


class BaseMetadataValidator(LoggingConfigurable):

    schema = None

    def __init__(self, version):
        if self.schema is None:
            with open(os.path.join(root, "v{:d}.json".format(version)), "r") as fh:
                self.schema = json.loads(fh.read())

    def upgrade_notebook_metadata(self, nb):
        for cell in nb.cells:
            self.upgrade_cell_metadata(cell)
        return nb

    def upgrade_cell_metadata(self, cell):
        raise NotImplementedError("this method must be implemented by subclasses")

    def validate_cell(self, cell):
        if 'nbgrader' not in cell.metadata:
            return
        schema = cell.metadata['nbgrader'].get('schema_version', 0)
        if schema != SCHEMA_VERSION:
            raise SchemaMismatchError(
                "outdated schema version: {} (expected {})".format(schema, SCHEMA_VERSION),
                schema, SCHEMA_VERSION)
        jsonschema.validate(cell.metadata['nbgrader'], self.schema)

    def validate_nb(self, nb):
        for cell in nb.cells:
            self.validate_cell(cell)
