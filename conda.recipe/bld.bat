"%PYTHON%" setup.py install --single-version-externally-managed --record=record.txt

CALL "%PREFIX%\Scripts\jupyter-nbextension" install --sys-prefix --overwrite --py nbgrader || EXIT /B 1
IF %ERRORLEVEL% NEQ 0 EXIT /B %ERRORLEVEL%
