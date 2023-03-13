from .common import ValidationError, SchemaTooOldError, SchemaTooNewError
from .v4 import MetadataValidatorV4 as MetadataValidator
from .v4 import read_v4 as read, write_v4 as write
from .v4 import reads_v4 as reads, writes_v4 as writes

SCHEMA_VERSION = MetadataValidator.schema_version

# Metadata required by latest schema, along with default values
SCHEMA_REQUIRED = {"schema_version": 4,
                   "grade": False,
                   "locked": False,
                   "solution": False}
