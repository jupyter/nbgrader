nbgrader and its exchange service
=================================

A simplistic overview
---------------------

``Assignments`` are ``created``, ``generated``, ``released``, ``fetched``, ``submitted``, ``collected``, ``graded``. Then ``feedback`` can be ``generated``, ``released``, and ``fetched``.

The exchange is responsible for recieving *released* assignments, allowing those assignments to be *fetched*, accepting *submissions*, and allowing those submissions to be *collected*. It also allows *feedback* to be transferred.

Calling exchange classes
~~~~~~~~~~~~~~~~~~~~~~~~

Exchange functions are called three ways:

1. From the command line - eg: ``nbgrader release_assignment assignment1``.
2. From **formgrader** server_extension, which generally calls the methods defined in ``nbgrader/apps/{foo}app.py``.
3. From the **assignment_list** server_extension, which generally calls the methods directly.



.. toctree::
    :maxdepth: 1
    :caption: Using an exchange

    exchange_api
    exchange_plugin