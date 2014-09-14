Upstream IPython:

* Make the main NbConvertApp easier to extend with custom config.
* Port directory walking to IPython.nbconvert.
* Figure out how to handle overwriting of notebook files.
* Modify Exporter.from_filename and other methods to track the path of the notebook as well.
* Find a way of propagating NbConvertApp level config attributes into resources.
* L243 of IPython.nbconvert.exporters.exporter passes a dict to ResourcesDict, which
  is a defaultdict subclass. The first argument of a defaultdict much as a callable.