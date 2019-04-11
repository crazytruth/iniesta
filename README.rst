=============================
iniesta
=============================

.. image:: https://badge.fury.io/py/iniesta.png
    :target: http://badge.fury.io/py/iniesta

.. image:: https://travis-ci.org/crazytruth/iniesta.png?branch=master
    :target: https://travis-ci.org/crazytruth/iniesta

Messaging integration for insanic

.. image:: docs/_static/iniesta.png

Why?
----

Iniesta is a messaging integration plugin for Insanic. Currently only supports AWS SNS
publish and AWS SQS polling.

Andrés Iniesta is a Spanish professional soccer player who plays as a central midfielder.
He is considered one the best players and one of the greatest midfielders of all time.
For those of you unfamiliar with soccer, a midfielder is responsible for passing the
soccer ball from the defense to the forwards.

Consequently, this project aims to be the best messaging between services; a proxy, for sending
messages(the soccer ball) from the producer(defenders) to the consumer(strikers).


Features
--------

* Asynchronous message handling
* Produce messages to a global SNS
* Filters for subscribing SQS to SNS
* Polling for SQS and receiving messages
* Decorator for consuming messages with defined parameters
* Locks for idempotent message handling.
* Checks for if proper subscribing has been setup
* Checks for if proper permissions has been setup


Installation
============

Prerequisites:

* python >= 3.6


To install:

.. code-block::

    pip install iniesta

To setup, we need a couple settings.

- `INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN`: (string) default:None The global sns arn.
- `INIESTA_SQS_CONSUMER_FILTERS`: (list) default:[] A list of filters for the message events your service will want to receive.
- `INIESTA_SNS_EVENT_KEY`: (string) default:iniesta_pass The key the event will be published under. Will NOT want to change this.
- `INIESTA_LOCK_RETRY_COUNT`: (int) default:1 Lock retry count when lock is unable to be required
- `INIESTA_LOCK_TIMEOUT`: (int) default:10s Timeout for the lock when received


.. inclusion-marker-do-not-remove-usage-start

Usage
=====

For Publishing Messages to SNS
******************************

For services that only need to produce SNS messages:

.. code-block:: python

    # in producing service named "producer"
    from insanic import Insanic
    from iniesta import Iniesta

    app = Insanic('producer')
    Iniesta.init_producer(app)
    # or
    # init_producer and prepare_for_delivering_through_pass are equivalent
    Iniesta.prepare_for_delivering_through_pass(app)

To produce messages:

.. code-block:: python

    # in producing service named "producer"
    from iniesta.sns import SNSClient

    sns = SNSClient(topic_arn)
    message = sns.create_message(event="EventHappened", message={"id": 1}, version=1)
    await message.publish()

    # or

    from iniesta.sns import SNSMessage

    sns = SNSClient(topic_arn)
    message = SNSMessage.create_message(sns, event="EventHappened", message={"id": 1})
    await message.publish()


This will publish a message to SNS with the event specified in the parameters.
The published event will be `{event}.{service_name}`. Even if you don't send the service_name,
it will automatically be appended.

For "SEND"ing messages to SQS
*****************************

Iniesta also allows messages to be sent to specific queues.

To send messages we first need to create a ``SQSMessage`` object.

.. code-block:: python

    from iniesta.sqs import SQSClient

    sqs = SQSClient() # if queue name is not specified it uses the services's default queue
    message = sqs.create_message(message="Hello") # returns SQSMessage instance
    await message.send()


For Consuming
*************

For consuming, we can setup 2 different types of polling methods.

1. Event Polling
    * Check if sqs has been created
    * Checks if global arn is set (`INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN`).
    * Checks if filters have been defined (`INIESTA_SQS_CONSUMER_FILTERS`).
    * Checks if subscriptions has been made with service sqs and sns.
    * Checks if necessary permissions have been put in place.


Initial setup for event polling:

.. code-block:: python

    # in service named receiver
    from insanic import Insanic
    from iniesta import Iniesta

    app = Insanic('receiver')
    Iniesta.init_event_polling(app)
    # or
    Iniesta.prepare_for_receiving_through_pass(app)


For creating a handler for a message:

.. code-block:: python

    # in consuming service named "receiver"
    from iniesta.sqs import SQSClient

    @SQSClient.handler('EventHappened.producer')
    def event_happened_handler(message):
        # .. do some logic ..
        return True

2. Queue Polling

Queue polling is only for receiving messages from an SQS, and does not get messages from SNS.

* Check if SQS has been created

.. code-block:: python

    # in service named receiver
    from insanic import Insanic
    from iniesta import Iniesta

    app = Insanic('receiver')
    Iniesta.init_queue_polling(app)
    # or
    Iniesta.prepare_for_receiving_short_pass(app)

For creating a default handler:

.. code-block:: python

    # in service `receiver`
    from iniesta.sqs import SQSClient

    @SQSClient.handler
    def default_handler(message):
        # .. do some stuff ..
        # might need to separate according to message type
        return True


Post Receiving Message
**********************

There are two paths for handling the message

1. On success, when the handler runs without any exceptions
    * The message will be deleted from the SQS Queue
    * can return from handler, but will be ignored

2. On exception raised,
    * will NOT delete message from SQS Queue
    * message will be available again for consumption after invisibility timeout

.. inclusion-marker-do-not-remove-usage-end

.. inclusion-marker-do-not-remove-commands-start

Commands
========

Several commands to help testing. All commands start with ``iniesta``

Setup
*****

.. code-block:: bash

    $ pip install iniesta[cli]

    $ iniesta --help
    Usage: iniesta [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      filter-policies
      initialization-type
      publish
      send

To get initialization type
**************************

.. code-block:: bash

    $ iniesta initialization-type
    InitializationTypes.SNS_PRODUCER|EVENT_POLLING

The returned values are:

- ``QUEUE_POLLING``
- ``EVENT_POLLING``
- ``SNS_PRODUCER``

or a combination of them.


To get filter policies
**********************

if ``INIESTA_SQS_CONSUMER_FILTERS = ['some.*']``

.. code-block:: bash

    $ iniesta filter-policies
    {"iniesta_pass": [{"prefix": "some."}]}

Test publishing to SNS
**********************

A CLI for sending a message to SNS Topic

Requirements:

- ``VAULT_ROLE_ID``
- ``MMT_ENV``

.. code-block:: bash

    $ iniesta publish --help
    Usage: iniesta publish [OPTIONS]

    Options:
      -e, --event TEXT       Event to publish into SNS  [required]
      -m, --message TEXT     Message body to publish into SNS  [required]
      -v, --version INTEGER  Version to publish into SNS
      --help                 Show this message and exit.

Test sending message to SQS
***************************

To send a custom message to a queue

Requirements:

- ``VAULT_ROLE_ID``
- ``MMT_ENV``

.. code-block:: bash

    $ iniesta send --help
    Usage: iniesta send [OPTIONS]

    Options:
      -m, --message TEXT  Message body to publish to SQS  [required]
      --help              Show this message and exit.

.. inclusion-marker-do-not-remove-commands-end

Development
===========

.. code-block:: bash

    pip install .[development]
    # or
    pip install iniesta[development]

Testing
=======

.. code-block:: bash

    $ pip install .[development]
    $ pytest
    # with coverage
    $ pytest --cov=iniesta --cov-report term-missing:skip-covered

To view documentation
=====================

.. code-block:: bash

    $ git clone https://github.com/MyMusicTaste/iniesta.git
    $ cd iniesta
    $ pip install .[development]
    $ cd docs
    $ make html
    # files will be in /path/to/iniesta/docs/_build


Release History
===============

View release history `here <HISTORY.rst>`_

TODO
----


