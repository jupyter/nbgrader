import json
import os
import jsonschema

from jsonschema import ValidationError
from traitlets.config import LoggingConfigurable
from nbformat.notebooknode import NotebookNode


root = os.path.dirname(__file__)


class SchemaMismatchError(Exception):

    def __init__(self, message, actual_version, expected_version):
        super(SchemaMismatchError, self).__init__(message)
        self.actual_version = actual_version
        self.expected_version = expected_version


class SchemaTooOldError(SchemaMismatchError):
    pass


class SchemaTooNewError(SchemaMismatchError):
    pass


class BaseMetadataValidator(LoggingConfigurable):

    def __init__(self) -> None:
        with open(os.path.join(root, "v{:d}.json".format(self.schema_version)), "r") as fh:
            self.schema = json.loads(fh.read())

    def _remove_extra_keys(self, cell: NotebookNode) -> None:
        meta = cell.metadata['nbgrader']
        allowed = set(self.schema["properties"].keys())
        keys = set(meta.keys()) - allowed
        if len(keys) > 0:
            self.log.warning("extra keys detected in metadata, these will be removed: {}".format(keys))
            for key in keys:
                del meta[key]

    def upgrade_notebook_metadata(self, nb: NotebookNode) -> NotebookNode:
        for cell in nb.cells:
            self.upgrade_cell_metadata(cell)
        return nb

    def upgrade_cell_metadata(self, cell: NotebookNode) -> NotebookNode:  # pragma: no cover
        raise NotImplementedError("this method must be implemented by subclasses")

    def validate_cell(self, cell: NotebookNode) -> None:
        if 'nbgrader' not in cell.metadata:
            return
        schema = cell.metadata['nbgrader'].get('schema_version', 0)
        if schema < self.schema_version:
            raise SchemaTooOldError(
                "Outdated schema version: {} (expected {})".format(schema, self.schema_version),
                schema, self.schema_version)
        elif schema > self.schema_version:
            raise SchemaTooNewError(
                "Schema version is too new: {} (expected {})".format(schema, self.schema_version),
                schema, self.schema_version)
        jsonschema.validate(cell.metadata['nbgrader'], self.schema)

    def validate_nb(self, nb: NotebookNode) -> None:
        for cell in nb.cells:
            self.validate_cell(cell)
