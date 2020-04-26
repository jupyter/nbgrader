# course_list

TODO: Populte README.

![Github Actions Status](https://github.com/lxylxy123456/nbgrader/workflows/Build/badge.svg)

Course list labextension for nbgrader


This extension is composed of a Python package named `course_list`
for the server extension and a NPM package named `course-list`
for the frontend extension.


## Requirements

* JupyterLab >= 2.0

## Install

Note: You will need NodeJS to install the extension.

```bash
pip install course_list
jupyter lab build
```

## Troubleshoot

If you are seeing the frontend extension but it is not working, check
that the server extension is enabled:

```bash
jupyter serverextension list
```

If the server extension is installed and enabled but you are not seeing
the frontend, check the frontend is installed:

```bash
jupyter labextension list
```

If it is installed, try:

```bash
jupyter lab clean
jupyter lab build
```

## Contributing

### Install

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Move to course_list directory

# Install server extension
pip install -e .
# Register server extension
jupyter serverextension enable --py course_list

# Install dependencies
jlpm
# Build Typescript source
jlpm build
# Link your development version of the extension with JupyterLab
jupyter labextension link .
# Rebuild Typescript source after making changes
jlpm build
# Rebuild JupyterLab after making any changes
jupyter lab build
```

You can watch the source directory and run JupyterLab in watch mode to watch for changes in the extension's source and automatically rebuild the extension and application.

```bash
# Watch the source directory in another terminal tab
jlpm watch
# Run jupyterlab in watch mode in one terminal tab
jupyter lab --watch
```

### Uninstall

```bash

pip uninstall course_list

jupyter labextension uninstall course-list
```
