=============================
iniesta
=============================

.. image:: https://badge.fury.io/py/iniesta.png
    :target: http://badge.fury.io/py/iniesta

.. image:: https://travis-ci.org/crazytruth/iniesta.png?branch=master
    :target: https://travis-ci.org/crazytruth/iniesta

Messaging integration for insanic

.. image:: iniesta.png

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


Usage
=====

For Producing
#############

For producing basic SNS messages:

.. code-block:: python

    # in producing service named "producer"
    from iniesta.sns import SNSClient

    sns = SNSClient(topic_arn)
    sns.publish_event(event="EventHappened", message={"id": 1},
                      version=1)

This will publish a message to SNS with the event specified in the parameters.
The published event will be `{event}.{service_name}`. Even if you don't send the service_name,
it will automatically be appended.

For Consuming
#############

Initial setup for polling SQS:

.. code-block:: python

    from insanic import Insanic
    from iniesta import Iniesta

    app = Insanic('service')
    Iniesta.init_app(app)


For creating a handler for a message:

.. code-block:: python

    # in consuming service named "consumer"
    from iniesta.sqs import SQSClient

    @SQSClient.handler('EventHappened.producer')
    def event_happened_handler(message):
        # .. do some logic ..
        return True

There are two paths for handling the message

1. On success, when the handler runs without any exceptions
    * The message will be deleted from the SQS Queue
    * can return from handler, but will be ignored

2. On exception raised,
    * will NOT delete message from SQS Queue
    * message will be available again for consumption after invisibility timeout


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

Release History
===============

View release history `here <HISTORY.rst>`_

TODO
----

* send message straight to sqs