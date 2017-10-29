SCHEMA_VERSION = 2

from .common import ValidationError, SchemaMismatchError
from .v2 import MetadataValidatorV2 as MetadataValidator
from .v2 import read_v2 as read, write_v2 as write
from .v2 import reads_v2 as reads, writes_v2 as writes
