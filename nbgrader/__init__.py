from __future__ import absolute_import

from .exporters import AssignmentExporter, FeedbackExporter
from IPython.nbconvert.exporters.export import exporter_map

exporter_map["assignment"] = AssignmentExporter
exporter_map["feedback"] = FeedbackExporter
