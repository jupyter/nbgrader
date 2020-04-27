# validate_assignment
Validate assignment button

## Requirements
* JupyterLab >= 2.0

## Install
```bash
jupyter labextension install validate-assignment
```

## Contributing

### Install
The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Move to validate_assignment directory

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

#### Disk space
If you have limited disk space, try running the following frequently
```
rm ~/.cache/yarn/v6/npm-validate-assignment-*
```

If your home directory is in SSD and you don't want it to be writen a lot
 each time you build your project:
```
sudo mount -t tmpfs tmpfs ~/.cache/yarn
```

### Uninstall
```bash
jupyter labextension uninstall validate-assignment
```

### Note
https://jupyterlab.readthedocs.io/en/stable/developer/notebook.html#how-to-extend-the-notebook-plugin
`npm install --save @jupyterlab/notebook @jupyterlab/application @jupyterlab/apputils @jupyterlab/docregistry @lumino/disposable`
`jlpm && jlpm build && jupyter labextension link .`
`jlpm watch`
`jupyter lab --watch`

