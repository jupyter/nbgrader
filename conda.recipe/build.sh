"${PYTHON}" setup.py install --single-version-externally-managed --record=record.txt

"${PREFIX}/bin/jupyter-nbextension" install --sys-prefix --overwrite --py nbgrader
