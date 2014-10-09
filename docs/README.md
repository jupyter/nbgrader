# Documentation

This README provides information on how to add and compile
documentation. If you are looking just to read the nbgrader user
documentation, take a look at it on
[nbviewer](http://nbviewer.ipython.org/github/jupyter/nbgrader/tree/master/docs/Index.ipynb).

## Adding documentation

All of nbgrader's documentation should be in the form of IPython
notebooks. These notebooks can include whatever is helpful: markdown,
code, etc. If a documentation notebook does include code or shell
commands, then it should be compiled **before** you add it to the
repository. To do this, `cd` to the root of the documentation
directory (this directory), and run:

```bash
make
```

This will run all of the documentation notebooks, so they are fully
up-to-date.
