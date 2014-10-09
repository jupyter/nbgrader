c = get_config()

c.NbConvertApp.export_format = 'notebook'
c.NbConvertApp.notebooks = ["*.ipynb"]
c.Exporter.preprocessors = ['IPython.nbconvert.preprocessors.ExecutePreprocessor']


