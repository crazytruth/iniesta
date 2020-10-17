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
      -m, --message TEXT     Message body to publish into SNS
      -v, --version INTEGER  Version to publish into SNS
      --help                 Show this message and exit.

Example
^^^^^^^

.. code-block:: sh

    $ iniesta publish -e hello.iniesta
    Publish Success!


    REQUEST INFO
    Message Event : hello.iniesta
    Message Data : {}
    Full Payload : {'MessageAttributes': {'iniesta_pass': {'DataType': 'String', 'StringValue': 'hello.iniesta'}, 'version': {'DataType': 'Number', 'StringValue': '1'}}, 'Message': '{}', 'MessageStructure': 'string'}
    Message Length : 183


    RESPONSE INFO
    Message ID : 4e2585df-dc90-49b5-a40f-10fac01c23aa
    Message Length : 291



Test sending message to SQS
----------------------------

To send a custom message to a queue

.. code-block:: bash

    $ iniesta send --help
    Usage: iniesta send [OPTIONS]

    Options:
      -m, --message TEXT  Message body to publish to SQS
      --help              Show this message and exit.

Example
^^^^^^^^

.. code-block:: sh

    $ iniesta send
    Message Sent
    MessageId: 0692141a-aee4-93fc-9b12-f0f5c5f313ac
