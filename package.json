{
  "name": "@jupyter/nbgrader",
  "version": "0.9.3",
  "description": "nbgrader nodejs dependencies",
  "keywords": [
    "jupyter",
    "jupyterlab",
    "jupyterlab-extension"
  ],
  "license": "BSD-3-Clause",
  "repository": {
    "type": "git",
    "url": "https://github.com/jupyter/nbgrader.git"
  },
  "author": {
    "name": "Jupyter Development Team",
    "email": "jupyter@googlegroups.com"
  },
  "files": [
    "lib/**/*.{d.ts,eot,gif,html,jpg,js,js.map,json,png,svg,woff2,ttf}",
    "style/**/*.{css,js,eot,gif,html,jpg,json,png,svg,woff2,ttf}",
    "schema/*.json"
  ],
  "main": "lib/index.js",
  "types": "lib/index.d.ts",
  "style": "style/index.css",
  "scripts": {
    "build": "jlpm build:lib && jlpm build:labextension:dev",
    "build:prod": "jlpm clean && jlpm build:lib && jlpm build:labextension",
    "build:labextension": "jupyter labextension build .",
    "build:labextension:dev": "jupyter labextension build --development True .",
    "build:lib": "tsc",
    "clean": "jlpm clean:lib",
    "clean:lib": "rimraf lib tsconfig.tsbuildinfo",
    "clean:labextension": "rimraf nbgrader/labextension",
    "clean:all": "jlpm clean:lib && jlpm clean:labextension",
    "install:labextension": "jlpm build",
    "start:test": "python ./nbgrader/tests/ui-tests/utils/run_jupyter_app.py",
    "test": "jlpm playwright test",
    "test:notebook": "NBGRADER_TEST_IS_NOTEBOOK=1 jlpm playwright test --config=playwright.notebook.config.ts",
    "watch": "run-p watch:src watch:labextension",
    "watch:src": "tsc -w",
    "watch:labextension": "jupyter labextension watch ."
  },
  "dependencies": {
    "@jupyter-notebook/application": "^7.2.0",
    "@jupyter-notebook/tree": "^7.2.0",
    "@jupyter/ydoc": "^2.0.0",
    "@jupyterlab/application": "^4.2.0",
    "@jupyterlab/apputils": "^4.3.0",
    "@jupyterlab/cells": "^4.2.0",
    "@jupyterlab/coreutils": "^6.2.0",
    "@jupyterlab/docregistry": "^4.2.0",
    "@jupyterlab/filebrowser": "^4.2.0",
    "@jupyterlab/mainmenu": "^4.2.0",
    "@jupyterlab/nbformat": "^4.2.0",
    "@jupyterlab/notebook": "^4.2.0",
    "@jupyterlab/observables": "^5.2.0",
    "@jupyterlab/services": "^7.2.0",
    "@jupyterlab/settingregistry": "^4.2.0",
    "@lumino/coreutils": "^2.1.2",
    "@lumino/disposable": "^2.1.2",
    "@lumino/messaging": "^2.0.1",
    "@lumino/signaling": "^2.1.2",
    "@lumino/widgets": "^2.3.2"
  },
  "devDependencies": {
    "@jupyterlab/builder": "^4.2.0",
    "@jupyterlab/galata": "^5.2.0",
    "@playwright/test": "^1.32.2",
    "@types/codemirror": "^5.60.5",
    "@typescript-eslint/eslint-plugin": "^5.0.0",
    "@typescript-eslint/parser": "^5.0.0",
    "bower": "*",
    "eslint": "^8.0.0",
    "eslint-config-prettier": "^8.0.0",
    "eslint-plugin-prettier": "^4.0.0",
    "mkdirp": "^1.0.4",
    "npm-run-all": "^4.1.5",
    "prettier": "^2.1.1",
    "react": "^18.2.0",
    "rimraf": "^3.0.2",
    "stylelint": "^14.3.0",
    "stylelint-config-prettier": "^9.0.3",
    "stylelint-config-recommended": "^6.0.0",
    "stylelint-config-standard": "~24.0.0",
    "stylelint-prettier": "^2.0.0",
    "typescript": "~5.0.4"
  },
  "sideEffects": [
    "style/*.css",
    "style/index.js"
  ],
  "styleModule": "style/index.js",
  "publishConfig": {
    "access": "public"
  },
  "jupyterlab": {
    "discovery": {
      "server": {
        "managers": [
          "pip"
        ],
        "base": {
          "name": "nbgrader"
        }
      }
    },
    "extension": true,
    "outputDir": "nbgrader/labextension",
    "schemaDir": "schema"
  },
  "packageManager": "yarn@3.5.0"
}
