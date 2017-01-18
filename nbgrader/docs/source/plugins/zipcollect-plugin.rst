ZipCollect plugins
==================

.. versionadded:: 0.5.0

FileNameProcessor plugin
------------------------

Apply a named group regular expression to each filename received from the
:class:`~nbgrader.apps.zipcollectapp.ZipCollectApp` and return ``None`` if the
file should be skipped or a :class:`~nbgrader.plugins.zipcollect.CollectInfo`
instance that, at the very least, contains the ``student_id`` and
``notebook_id`` data; and optionally contains the ``timestamp``,
``first_name``, ``last_name``, and ``email`` data.

For more information about named group regular expressions see
`<https://docs.python.org/howto/regex.html>`_

Creating a plugin
-----------------

To add your own processor you can create a plugin class that inherits from
:class:`~nbgrader.plugins.zipcollect.FileNameProcessor`. This class needs to
only implement one method, which is the
:func:`~nbgrader.plugins..zipcollect.FileNameProcessor.collect` method (see
below). Let's say you create your own plugin in the ``myprocessor.py`` file,
and your plugin is called ``MyProcessor``. Then, on the command line, you would
run::

    nbgrader zip_collect --processor=myprocessor.MyProcessor

which will use your custom processor rather than the built-in one.

API
---

.. currentmodule:: nbgrader.plugins.zipcollect

.. autoclass:: CollectInfo

.. autoclass:: FileNameProcessor

    .. automethod:: collect
