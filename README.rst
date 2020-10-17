.. image:: https://github.com/crazytruth/iniesta/raw/master/docs/source/_static/iniesta.png

*******
Iniesta
*******

|Build Status| |Documentation Status| |Codecov|

|PyPI pyversions| |PyPI version| |PyPI license| |Black|

.. |Build Status| image:: https://github.com/crazytruth/iniesta/workflows/Python%20Tests/badge.svg
    :target: https://github.com/crazytruth/iniesta/actions?query=workflow%3A%22Python+Tests%22

.. |Documentation Status| image:: https://readthedocs.org/projects/iniesta/badge/?version=latest
    :target: http://iniesta.readthedocs.io/?badge=latest

.. |Codecov| image:: https://codecov.io/gh/crazytruth/iniesta/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/crazytruth/iniesta

.. |PyPI version| image:: https://img.shields.io/pypi/v/iniesta-framework
    :target: https://pypi.org/project/insanic-iniesta/

.. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/insanic-framework
    :target: https://pypi.org/project/insanic-iniesta/

.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |PyPI license| image:: https://img.shields.io/github/license/crazytruth/iniesta?style=flat-square
    :target: https://pypi.org/project/insanic-iniesta/

.. end-badges

A messaging integration for the event driven pattern utilizing AWS SNS and AWS SQS for `Insanic`_.


Why?
=====

Iniesta is a messaging integration plugin for `Insanic`_. This was initially created to easily apply
the event driven pattern to services running `Insanic`_.

For a bit of context, Andrés Iniesta is a Spanish professional soccer player who plays as a central midfielder.
He is considered one the best soccer players and one of the greatest midfielders of all time.
For those of you unfamiliar with soccer, a midfielder is responsible for playmaking, passing the
soccer ball from the defense to the forwards.

Consequently, this project aims to be the messenger between services; a proxy, for sending
messages(the soccer ball) from the producers(defenders) to the consumer(strikers) albeit
the messages fan out and there is only one soccer ball.


Features
=========

- Asynchronous message handling.
- Produce messages to a global SNS.
- Filters for verification and subscribing SQS to SNS.
- Polling for SQS and receiving messages.
- Decorator for consuming messages with defined parameters.
- Locks for idempotent message handling.
- Checks for if proper subscriptions have been setup.
- Checks for if proper permissions has been setup.
- Decorators for emitting messages.


Installation
=============

Prerequisites:

- python >= 3.6
- AWS Credentials


To install:

.. code-block:: bash

    pip install insanic-iniesta

To setup, we need a couple settings.

- :code:`INIESTA_INITIALIZATION_TYPE` : (list[string]) List of initialization types defined by `InitializationTypes` enum.

    - Choices: "QUEUE_POLLING", "EVENT_POLLING", "SNS_PRODUCER", "CUSTOM"

- :code:`INIESTA_SQS_CONSUMER_FILTERS`: (list) default:[] A list of filters for the message events your service will want to receive.
- :code:`INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN`: (string) default:None The global sns arn.
- :code:`INIESTA_SNS_EVENT_KEY`: (string) default:iniesta_pass The key the event will be published under. Will NOT want to change this.
- :code:`INIESTA_LOCK_RETRY_COUNT`: (int) default:1 Lock retry count when lock is unable to be required
- :code:`INIESTA_LOCK_TIMEOUT`: (int) default:10s Timeout for the lock when received


Basic Usage
===========

There are several initialization types because not all applications
need to produce, or receive messages at the same time.  So you would need
to set the initialization type catered towards your use case.

Initializing
------------

First we need to decide on the type of initialization we need
to use.  For Iniesta to know the initialization type,
we need to set :code:`INIESTA_INITIALIZATION_TYPE` in our
config. Until we do so, you will not be able to run
Insanic.

.. code-block:: python

    # in your application config.py
    INIESTA_INITIALIZATION_TYPE = ["SNS_PRODUCER"]

    # and finally in app.py
    from insanic import Insanic
    from iniesta import Iniesta

    app = Insanic('producer', version="0.0.1")
    Iniesta.init_app(app)

For more documentation on initialization types,
please refer to the Iniesta's `Documentation`_.


Publishing Messages to SNS
--------------------------

You would want to setup Iniesta if you ONLY need to
produce messages to SNS.

.. code-block:: python

    from iniesta.sns import SNSClient

    sns = SNSClient(topic_arn)
    message = sns.create_message(event="EventHappened", message={"id": 1}, version=1)
    await message.publish()

This will publish a message to SNS with the event
specified in the parameters. The published event will be
:code:`{event}.{service_name}`. Even if you don't specify the service_name in
the event, it will automatically be appended.


Consuming Messages
------------------

To consume messages that other applications have produced,
we setup Iniesta for :code:`EVENT_POLLING`.

There are several checks Iniesta performs when
initializing for :code:`EVENT_POLLING`.

- Checks if the AWS SQS has been created.
- Checks if global arn is set (:code:`INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN`)
- Checks if filters have been defined (:code:`INIESTA_SQS_CONSUMER_FILTERS`).
- Checks if subscriptions has been made with service SQS and SNS.
- Checks if necessary permissions have been put in place.

Initial setup for event polling:

.. code-block:: python

    # in your config.py
    INIESTA_INITIALIZATION_TYPE = ['EVENT_POLLING']

    # in service named receiver
    from insanic import Insanic
    from iniesta import Iniesta

    app = Insanic('receiver')
    Iniesta.init_app(app)


Since we have initialized for polling our queue, we need to
create handlers for processing the messages.

For creating a handler for an event:

.. code-block:: python

    from iniesta.sqs import SQSClient

    @SQSClient.handler('EventHappened.producer')
    def event_happened_handler(message):
        # .. do some logic ..
        pass

The function must receive :code:`message` as an argument.
If the function successfully runs, the message will be
deleted from SQS.

Other Use Cases
----------------

For other use cases for Iniesta, please refer to the `Documentation`_.


Commands
========

Iniesta provides several commands to help testing during
development.

Install
-------
.. code-block:: bash

    $ pip install iniesta[cli]

Basic Usage
-----------

.. code-block:: bash

    $ iniesta --help
    Usage: iniesta [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      filter-policies
      initialization-type
      publish
      send


Please refer to the Iniesta's `Commands Documentation`_ for
more information on each of the available commands.


Known Issues
=============

- If the module including the handlers are not imported, they do not properly register.
    To prevent this import the module somewhere(e.g. in your `app.py`) until
    a better solution is found.

Release History
===============

View release history `here <CHANGELOG.rst>`_


Contributing
=============

For guidance on setting up a development environment and how to make a contribution to Iniesta,
see the `CONTRIBUTING.rst <CONTRIBUTING.rst>`_ guidelines.


Meta
====

Distributed under the MIT license. See `LICENSE <LICENSE>`_ for more information.

Thanks to all the people at my prior company that worked with me to make this possible.

Links
=====

- Documentation: https://iniesta.readthedocs.io/en/latest/
- Releases: https://pypi.org/project/insanic-iniesta/
- Code: https://www.github.com/crazytruth/iniesta/
- Issue Tracker: https://www.github.com/crazytruth/iniesta/issues
- Insanic Documentation: http://insanic.readthedocs.io/
- Insanic Repository: https://www.github.com/crazytruth/insanic/

.. _Insanic: https://github.com/crazytruth/insanic
.. _Documentation: https://iniesta.readthedocs.io/en/latest/
.. _Commands Documentation: https://iniesta.readthedocs.io/en/latest/iniesta/commands/
