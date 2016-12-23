$PYTHON setup.py install

"${PREFIX}/bin/jupyter-nbextension" install --sys-prefix --overwrite --py nbgrader
