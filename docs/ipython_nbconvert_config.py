c = get_config()

c.NbConvertApp.export_format = 'notebook'
c.Exporter.preprocessors = ['IPython.nbconvert.preprocessors.ExecutePreprocessor']
