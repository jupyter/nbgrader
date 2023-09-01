Advanced topics
===============

This file covers some more advanced use cases of nbgrader.

.. contents:: Table of contents
   :depth: 2

Running nbgrader with JupyterHub
--------------------------------

Please see :doc:`/configuration/jupyterhub_config`.

.. _assignment-list-installation:

Advanced "Assignment List" installation
---------------------------------------

.. seealso::

  :doc:`installation`
    General installation instructions.

  :doc:`managing_assignment_files`
    Details on fetching and submitting assignments using the "Assignment List"
	plugin.

.. warning::

  The "Assignment List" extension is not currently compatible with multiple
  courses on the same server: it will only work if there is a single course on
  the server. This is a known issue (see `#544
  <https://github.com/jupyter/nbgrader/issues/544>`__). :ref:`PRs welcome!
  <pull-request>`

This section covers some further and configuration scenarios that often
occur with the *assignment list* extension.

In previous versions of nbgrader, a special process had to be used to enable
this extension for all users on a multi-user system. As described in the main
:doc:`installation` documentation this is no longer required.

If you know you have released an assignment but still don't see it in the list
of assignments, check the output of the notebook server to see if there are any
errors. If you do in fact see an error, try running the command manually on the
command line from the directory where the notebook server is running. For
example:

.. code:: bash

  $ nbgrader list
  [ListApp | ERROR] Unwritable directory, please contact your instructor: /usr/local/share/nbgrader/exchange

This error that the exchange directory isn't writable is an easy mistake to
make, but also relatively easy to fix. If the exchange directory is at
``/usr/local/share/nbgrader/exchange``, then make sure you have run:

.. code:: bash

  chmod ugo+rw /usr/local/share/nbgrader/exchange

.. _getting-information-from-db:

Getting information from the database
-------------------------------------

nbgrader offers a fairly rich :doc:`API </api/index>` for interfacing with the
database. The API should allow you to access pretty much anything you want,
though if you find something that can't be accessed through the API please
`open an issue <https://github.com/jupyter/nbgrader/issues/new>`_!

In this example, we'll go through how to create a CSV file of grades for each
student and assignment using nbgrader and `pandas
<https://pandas.pydata.org/>`__.

.. versionadded:: 0.4.0
    nbgrader now comes with CSV export functionality out-of-the box using the
    :doc:`nbgrader export </command_line_tools/nbgrader-export>` command.
    However, this example is still kept for reference as it may be useful for
    :doc:`defining your own exporter </plugins/export-plugin>`.

.. literalinclude:: extract_grades.py
   :language: python

After running the above code, you should see that ``grades.csv`` contains something that looks like::

    student,assignment,max_score,score
    bitdiddle,ps1,9.0,1.5
    hacker,ps1,9.0,3.0

Using nbgrader preprocessors
----------------------------

Several of the nbgrader preprocessors can be used with nbconvert without
actually relying on the rest of the nbgrader machinery. In particular, the
following preprocessors can be applied to other nbconvert workflows:

- ``ClearOutput`` -- clears outputs of all cells
- ``ClearSolutions`` -- removes solutions between the
  solution delimeters (see :ref:`autograded-answer-cells`).
- ``HeaderFooter`` -- concatenates notebooks together,
  prepending a "header" notebook and/or appending a "footer" notebook to
  another notebook.
- ``LimitOutput`` -- limits the amount of output any given
  cell can have. If a cell has too many lines of outputs, they will be
  truncated.

Using these preprocessors in your own nbconvert workflow is relatively
straightforward. In your ``nbconvert_config.py`` file, you would add, for
example:

.. code:: python

    c.Exporter.preprocessors = ['nbgrader.preprocessors.ClearSolutions']

See also the nbconvert docs on `custom preprocessors <https://nbconvert.readthedocs.io/en/latest/nbconvert_library.html#Custom-Preprocessors>`__.

Calling nbgrader apps from Python
---------------------------------

.. versionadded:: 0.5.0
    Much of nbgrader's high level functionality can now be accessed through
    an official :doc:`Python API </api/high_level_api>`.

.. _grading-in-docker:

Grading in a docker container
-----------------------------

For security reasons, it may be advantageous to do the grading with a kernel
running in isolation, e.g. in a docker container. We will assume that
docker is already installed and an appropriate image has been downloaded.
Otherwise, refer to the `docker documentation <https://docs.docker.com>`_
for information on how to install and run docker.

A convenient way to switch to a kernel running in a docker container is
provided by ``envkernel`` which serves a double purpose. In a first step,
it is writing a new kernelspec file. Later it ensures that the docker
container is run and the kernel started.

Presently, ``envkernel`` is only available from its `Github repository
<https://github.com/NordicHPC/envkernel>`_ and can be installed directly
from there into a virtual environment

.. code:: bash

    pip install https://github.com/NordicHPC/envkernel/archive/master.zip

As an alternative, the script ``envkernel.py`` can be put in a different
location, e.g. ``/opt/envkernel``, as long as it is accessible there also
later during grading.

Now, a new kernel can be installed by means of

.. code:: bash

    ./envkernel.py docker --name=NAME --display-name=DNAME DOCKER-IMAGE

Here, ``NAME`` should be replaced by the name to be given to the kernel.
After installation of the kernel, it will be displayed in the list of
kernels when executing ``jupyter kernelspec list``.  ``DNAME`` should be
replaced by the name under which the kernel shall be known in the Jupyter
notebook GUI. After installation of the kernel, this name will be listed as
a possible kernel when starting a new notebook. Finally, ``DOCKER-IMAGE``
should be replaced by the name of the docker image in which the kernel is
to be run, e.g. ``python:3``, ``continuumio/anaconda3``, or some other
suitable image.

The command given above will install the kernel in the system-wide location
for Jupyter data files. If installation in the corresponding user directory
is desired, the option ``--user`` should be added before the name of the
docker image. By default, ``envkernel`` will install a Python kernel. For
the installation of other kernels, see the `README
<https://github.com/NordicHPC/envkernel/blob/master/README.md>`_ of
``envkernel``.

In order to run the grading process with the new kernel, one can specify
its name in ``nbgrader_config.py``

.. code:: python

    c.ExecutePreprocessor.kernel_name = NAME

where ``NAME`` should be replaced by the name chosen when running the
``envkernel`` script. Alternatively, the name can be specified when running
nbgrader from the command line

.. code:: bash

    nbgrader autograde --ExecutePreprocessor.kernel_name=NAME ASSIGNMENT_NAME

In addition to docker, ``envkernel`` also supports singularity as a
containerization system. For details on using ``envkernel`` with
singularity, see the `README
<https://github.com/NordicHPC/envkernel/blob/master/README.md>`_ of
``envkernel``.

.. _customizing-autotests:

Automatic test code generation
---------------------------------------

.. versionadded:: 0.9.0

.. seealso::

  :ref:`autograder-tests-cell-automatic-test-code`
    General introduction to automatic test code generation.


nbgrader now supports generating test code automatically
using ``### AUTOTEST`` and ``### HASHED AUTOTEST`` statements.
In this section, you can find more detail on how this works and 
how to customize the test generation process. 
Suppose you ask students to create a ``foo`` function that adds 5 to
an integer. In the source copy of the notebook, you might write something like

.. code:: python
    
    ### BEGIN SOLUTION
    def foo(x):
      return x + 5
    ### END SOLUTION

In a test cell, you would normally then write test code manually to probe various aspects of the solution.
For example, you might check that the function increments 3 to 8 properly, and that the type
of the output is an integer.

.. code:: python

    assert isinstance(foo(3), int), "incrementing an int by 5 should return an int"
    assert foo(3) == 8, "3+5 should be 8"

nbgrader now provides functionality to automate this process. Instead of writing tests explicitly,
you can instead specify *what you want to test*, and let nbgrader decide *how to test it* automatically.

.. code:: python

    ### AUTOTEST foo(3)

This directive indicates that you want to check ``foo(3)`` in the student's notebook, and make sure it 
aligns with the value of ``foo(3)`` in the current source copy. You can write any valid expression (in the 
language of your notebook) after the ``### AUTOTEST`` directive. For example, you could write

.. code:: python

   ### AUTOTEST (foo(3) - 5 == 3)

to generate test code for the expression ``foo(3)-5==3`` (i.e., a boolean value), and make sure that evaluating
the student's copy of this expression has a result that aligns with the source version (i.e., ``True``). You can write multiple
``### AUTOTEST`` directives in one cell. You can also separate multiple expressions on one line with semicolons:

.. code:: python

   ### AUTOTEST foo(3); foo(4); foo(5) != 8

These directives will insert code into student notebooks where the solution is available in plaintext. If you want to
obfuscate the answers in the student copy, you should instead use a ``### HASHED AUTOTEST``, which will produce
a student notebook where the answers are hashed and not viewable by students.

When you generate an assignment containing ``### AUTOTEST`` (or ``### HASHED AUTOTEST``) statements, nbgrader looks for a file
named ``autotests.yml`` that contains instructions on how to generate test code. It first looks 
in the assignment directory itself (in case you want to specify special tests for just that assignment), and if it is 
not found there, nbgrader searches in the course root directory.
The ``autotests.yml`` file is a `YAML <https://yaml.org/>`__ file that looks something like this:

.. code:: yaml

    python3:
        setup: "from hashlib import sha1"
        hash: 'sha1({{snippet}}.encode("utf-8")+b"{{salt}}").hexdigest()'
        dispatch: "type({{snippet}})"
        normalize: "str({{snippet}})"
        check: 'assert {{snippet}} == """{{value}}""", """{{message}}"""'
        success: "print('Success!')"

        templates:
            default:
                - test: "type({{snippet}})"
                  fail: "type of {{snippet}} is not correct"

                - test: "{{snippet}}"
                  fail: "value of {{snippet}} is not correct"

            int:
                - test: "type({{snippet}})"
                  fail: "type of {{snippet}} is not int. Please make sure it is int and not np.int64, etc. You can cast your value into an int using int()"

                - test: "{{snippet}}"
                  fail: "value of {{snippet}} is not correct"

The outermost  level in the YAML file (the example shows an entry for ``python3``) specifies which kernel the configuration applies to. ``autotests.yml`` can 
have separate sections for multiple kernels / languages. The ``autotests.yml`` file uses `Jinja templates <https://jinja.palletsprojects.com/en/3.1.x/>`__ to 
specify snippets of code that will be executed/inserted into Jupyter notebooks in the process of generating the assignment. You should familiarize yourself 
with the basics of Jinja templates before proceeding. For each kernel, there are a few configuration settings possible:

- **dispatch:** When you write ``### AUTOTEST foo(3)``, nbgrader needs to know how to test ``foo(3)``. It does so by executing ``foo(3)``, then checking its *type*,
  and then running tests corresponding to that type in the ``autotests.yml`` file. Specifically, when generating an assignment, nbgrader substitutes the ``{{snippet}}`` template
  variable with the expression ``foo(3)``, and then evaluates the dispatch code based on that. In this case, nbgrader runs ``type(foo(3))``, which will 
  return ``int``, so nbgrader will know to test ``foo(3)`` using tests for integer variables.
- **templates:** Once nbgrader determines the type of the expression ``foo(3)``, it will look for that type in the list of templates for the kernel. In this case,
  it will find the ``int`` type in the list (it will use the **default** if the type is not found). Each type will have associated with it a 
  list of **test**/**fail** template pairs, which tell nbgrader what tests to run 
  and what messages to print in the event of a failure. Once again, ``{{snippet}}`` will be replaced by the ``foo(3)`` expression. In ``autotests.yml`` above, the 
  ``int`` type has two tests: one that checks type of the expression, and one that checks its value. In this case, the student notebook will have 
  two tests: one that checks the value of ``type(foo(3))``, and one that checks the value of ``foo(3)``.
- **normalize:** For each test code expression (for example, ``type(foo(3))`` as mentioned previously), nbgrader will execute code using the corresponding 
  Jupyter kernel, which will respond with a result in the form of a *string*. So nbgrader now knows that if it runs ``type(foo(3))`` at this 
  point in the notebook, and converts the output to a string (i.e., *normalizes it*), it should obtain ``"int"``. However, nbgrader does not know how to convert output to a string; that
  depends on the kernel! So the normalize code template tells nbgrader how to convert an expression to a string. In the ``autotests.yml`` example above, the 
  normalize template suggests that nbgrader should try to compare ``str(type(foo(3)))`` to ``"int"``. 
- **check:** This is the code template that will be inserted into the student notebook to run each test. The template has three variables. ``{{snippet}}`` is the normalized
  test code. The ``{{value}}`` is the evaluated version of that test code, based on the source notebook. The ``{{message}}`` is
  text that will be printed in the event of a test failure. In the example above, the check code template tells nbgrader to insert an ``assert`` statement to run the test.
- **hash (optional):** This is a code template that is responsible for hashing (i.e., obfuscating) the answers in the student notebok. The template has two variables.
  ``{{snippet}}`` represents the expression that will be hashed, and ``{{salt}}`` is used for nbgrader to insert a `salt <https://en.wikipedia.org/wiki/Salt_(cryptography)>`__ 
  prior to hashing. The salt helps avoid students being able to identify hashes from common question types. For example, a true/false question has only two possible answers;
  without a salt, students would be able to recognize the hashes of ``True`` and ``False`` in their notebooks. By adding a salt, nbgrader makes the hashed version of the answer 
  different for each question, preventing identifying answers based on their hashes.
- **setup (optional):** This is a code template that will be run at the beginning of all test cells containing ``### AUTOTEST`` or ``### HASHED AUTOTEST`` directives. It is often used to import
  special packages that only the test code requires. In the example above, the setup code is used to import the ``sha1`` function from ``hashlib``, which is necessary
  for hashed test generation.
- **success (optional):** This is a code template that will be added to the end of all test cells containing ``### AUTOTEST`` or ``### HASHED AUTOTEST`` directives. In the 
  generated student version of the notebook,
  this code will run if all the tests pass. In the example ``autotests.yml`` file above, the success code is used to run ``print('Success!')``, i.e., simply print a message to
  indicate that all tests in the cell passed.

.. note::

   For assignments with ``### AUTOTEST`` and ``### HASHED AUTOTEST`` directives, it is often handy
   to have an editable copy of the assignment with solutions *and* test code inserted. You can
   use ``nbgrader generate_assignment --source_with_tests`` to generate this version of an assignment,
   which will appear in the ``source_with_tests/`` folder in the course repository.

.. warning::

   The default ``autotests.yml`` test templates file included with the repository has tests for many
   common data types (``int``, ``dict``, ``list``, ``float``, etc). It also has a ``default`` test template
   that it will try to apply to any types that do not have specified tests. If you want to automatically
   generate your own tests for custom types, you will need to implement those test templates in ``autotests.yml``. That being said, custom
   object types often have standard Python types as class attributes. Sometimes an easier option is to use nbgrader to test these
   attributes automatically instead. For example, if ``obj`` is a complicated type with no specific test template available,
   but ``obj`` has an ``int`` attribute ``x``, you could consider testing that attribute directly, e.g., ``### AUTOTEST obj.x``.

.. warning::

   The InstantiateTests preprocessor in nbgrader is responsible for generating test code from ``### AUTOTEST`` 
   directives and the ``autotests.yml`` file. It has some configuration parameters not yet mentioned here.
   The most important of these is the ``InstantiateTests.sanitizers`` dictionary, which tells nbgrader how to 
   clean up the string output from each kind of Jupyter kernel before using it in the process of generating tests. We have 
   implemented sanitizers for popular kernels in nbgrader already, but you might need to add your own.


