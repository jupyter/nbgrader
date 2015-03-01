from exporters import AssignmentExporter
from IPython.nbconvert.exporters.export import exporter_map
exporter_map["assignment"] = AssignmentExporter
