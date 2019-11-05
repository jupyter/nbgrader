
import hashlib

from traitlets import Bool
from .exchange import Exchange


def _checksum(path):
    m = hashlib.md5()
    m.update(open(path, 'rb').read())
    return m.hexdigest()


class ExchangeList(Exchange):

    inbound = Bool(False, help="List inbound files rather than outbound.").tag(config=True)
    cached = Bool(False, help="List assignments in submission cache.").tag(config=True)
    remove = Bool(False, help="Remove, rather than list files.").tag(config=True)

    def parse_assignment(self, assignment):
        pass

    def format_inbound_assignment(self, info):
        pass

    def format_outbound_assignment(self, info):
        pass

    def parse_assignments(self):
        pass

    def list_files(self):
        pass

    def remove_files(self):
        pass
