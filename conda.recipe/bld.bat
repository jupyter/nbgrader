"%PYTHON%" setup.py install
if errorlevel 1 exit 1

CALL "%PREFIX%\Scripts\jupyter-nbextension" install --sys-prefix --overwrite --py nbgrader || EXIT /B 1
IF %ERRORLEVEL% NEQ 0 EXIT /B %ERRORLEVEL%
