# Documentation

This README provides information on how to add and compile
documentation. If you are looking just to read the nbgrader user
documentation, take a look at it on
[nbviewer](http://nbviewer.ipython.org/github/jupyter/nbgrader/tree/docs/Index.ipynb).

## Adding documentation

All of nbgrader's documentation should be in the form of IPython
notebooks. These notebooks can include whatever is helpful: markdown,
code, etc. Notebooks should only ever be committed to the repository
with their output cleared first. Travis CI will automatically run
the notebooks and push the results to the `docs` branch.
