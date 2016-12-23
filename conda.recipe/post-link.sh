{
  "${PREFIX}/bin/jupyter-nbextension" enable --sys-prefix --py nbgrader
  "${PREFIX}/bin/jupyter-serverextension" enable --sys-prefix --py nbgrader
} >>"$PREFIX/.messages.txt" 2>&1
