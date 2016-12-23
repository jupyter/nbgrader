{
  "${PREFIX}/bin/jupyter-nbextension" disable --sys-prefix --py nbgrader
  "${PREFIX}/bin/jupyter-serverextension" disable --sys-prefix --py nbgrader
} >>"$PREFIX/.messages.txt" 2>&1
