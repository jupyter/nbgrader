{
  "${PREFIX}/bin/jupyter-nbextension" disable --sys-prefix --py nbgrader
} >>"$PREFIX/.messages.txt" 2>&1
