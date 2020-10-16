CLI Commands
=============

Iniesta provides some commands available for just testing
out your implementation of Iniesta and also some helper
commands for determining how your application is set up.


To get initialization type
---------------------------

.. code-block:: bash

    $ iniesta initialization-type
    InitializationTypes.SNS_PRODUCER|EVENT_POLLING

The returned values are:

- :code:`InitializationTypes.0`
- :code:`InitializationTypes.QUEUE_POLLING`
- :code:`InitializationTypes.EVENT_POLLING`
- :code:`InitializationTypes.SNS_PRODUCER`
- :code:`InitializationTypes.CUSTOM`

or a combination of them. eg

- :code:`InitializationTypes.SNS_PRODUCER|EVENT_POLLING`


To get filter policies
-----------------------

if :code:`INIESTA_SQS_CONSUMER_FILTERS = ['some.*']`

.. code-block:: bash

    $ iniesta filter-policies
    {"iniesta_pass": [{"prefix": "some."}]}


Test publishing
---------------

A CLI for sending a message to a SNS Topic.

Requirements:

.. code-block:: bash

    $ iniesta publish --help
    Usage: iniesta publish [OPTIONS]

    Options:
      -e, --event TEXT       Event to publish into SNS  [required]
      -m, --message TEXT     Message body to publish into SNS  [required]
      -v, --version INTEGER  Version to publish into SNS
      --help                 Show this message and exit.

Test sending message to SQS
----------------------------

To send a custom message to a queue

.. code-block:: bash

    $ iniesta send --help
    Usage: iniesta send [OPTIONS]

    Options:
      -m, --message TEXT  Message body to publish to SQS  [required]
      --help              Show this message and exit.
