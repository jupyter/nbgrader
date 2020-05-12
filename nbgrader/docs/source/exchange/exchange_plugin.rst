Using an alternative exchange
=============================

By default, the exchange assumes all users are unique on the host, and uses folders and *file-copys* to manage the distribution of files.

nbgrader will, however, allow alternative mechanisms for distribution.

The default exchange
--------------------

The exchange package is organised as follows::

    exchange/
    ├── abc/
    │   ├── collect.py
    │   ├── ...
    │   └── submit.py
    ├── default/
    │   ├── collect.py
    │   ├── ...
    │   └── submit.py
    └── exchange_factory.py

The ``exchange.abc`` package contains all the Abstract Base Classes that custom exchange packages need to implement.
The ``exchange.default`` package is a default filesystem based implementation. The exchange_factory.py file contains
the defintion for the ExchangeFactory class that is used to create instances of the exchange classes.

The nbgrader exchange uses the followng classes::

    Exchange
    ExchangeError
    ExchangeCollect
    ExchangeFetch
    ExchangeFetchAssignment
    ExchangeFetchFeedback
    ExchangeList
    ExchangeRelease
    ExchangeReleaseAssignment
    ExchangeReleaseFeedback
    ExchangeSubmit

Of these ExchangeFetch and ExchangeRelease have both been deprecated and not configurable through the ExchangeFactory class.

Configuring a custom exchange
-----------------------------

To configure a custom exchange, you simply set the relevant field in the ExchangeFactory class through traitlets configuration service.

For example, if we have installed a package called ``nbexchange``, we add the following to the ``nbgrader_config.py`` file::

        ## A plugin for collecting assignments.
        c.ExchangeFactory.collect = 'nbexchange.plugin.ExchangeCollect'
        ## A plugin for exchange.
        c.ExchangeFactory.exchange = 'nbexchange.plugin.Exchange'
        ## A plugin for fetching assignments.
        c.ExchangeFactory.fetch_assignment = 'nbexchange.plugin.ExchangeFetchAssignment'
        ## A plugin for fetching feedback.
        c.ExchangeFactory.fetch_feedback = 'nbexchange.plugin.ExchangeFetchFeedback'
        ## A plugin for listing exchange files.
        c.ExchangeFactory.list = 'nbexchange.plugin.ExchangeList'
        ## A plugin for releasing assignments.
        c.ExchangeFactory.release_assignment = 'nbexchange.plugin.ExchangeReleaseAssignment'
        ## A plugin for releasing feedback.
        c.ExchangeFactory.release_feedback = 'nbexchange.plugin.ExchangeReleaseFeedback'
        ## A plugin for submitting assignments.
        c.ExchangeFactory.submit = 'nbexchange.plugin.ExchangeSubmit'

The fields in the ExchangeFactory are:

* ``exchange`` - The base Exchange class that all other classes inherit from
* ``fetch_assignment`` - The ExchangeFetchAssignment class
* ``fetch_feedback`` - The ExchangeFetchFeedback class
* ``release_assignment`` - The ExchangeReleaseAssignment class
* ``release_feedback`` - The ExchangeReleaseFeedback class
* ``list`` - The ExchangeList class
* ``submit`` - The ExchangeSubmit class
* ``collect`` - The ExchangeCollect class