================
Message Handlers
================

For how to handle messages received by iniesta, we attach handlers.

Prerequisites
=============

- the function must be able to receive a ``message`` argument.

Usage
=====

There are two ways to attach handlers

- Decorators

.. code-block:: python

    # in handlers.py
    from iniesta.sqs import SQSClient

    @SQSClient.handler("SomethingHappened.somewhere")
    def something_happened_handler(message):
        # .. do some logic
        return

To a class method.

.. code-block:: python

    from iniesta.sqs import SQSClient

    class Handlers:

        @SQSClient.handler('SomethingHappened.elsewhere')
        def something_happened_handler(self, message):
            # .. some logic
            pass

- Attach directly

.. code-block:: python

    # in handlers.py

    from iniesta.sqs import SQSClient

    def something_else_happened_handler(message):
        # do some logic
        return

    SQSClient.add_handler(something_else_happened_handler,
                          "SomethingElseHappened.nowhere")

Attach handler for an Event
---------------------------

Both ``SQSClient.handler`` and ``SQSClient.add_handler`` both are
able to take an event as an argument.

In the case that iniesta receives a message from SQS, the ``SQSClient``
determines what to do with the message according to the "event" attached
to the message attributes of the message.  The current default is
``iniesta_pass`` defined in the ``INIESTA_SNS_EVENT_KEY`` config.

If we get a message like so:

.. code-block:: json

    {
        "MessageAttributes":
        {
            "iniesta_pass": "UserUpdated.user"},
            ... redacted
        },
        ... redacted
    }

and we attach a handler like so:

.. code-block:: python

    @SQSClient.handler("UserUpdated.user")
    def user_updated_handler(message):
        # some logic
        pass

The ``user_updated_handler`` function will be called.

Attach a default handler
------------------------

In the case where you would like to attach a fallback and/or have queue polling setup,
you only need to attach or decorate a function without any arguments.

.. code-block:: python

    @SQSClient.handler
    def default_handler(message):
        # depending on what kind of message do some logic
        pass

Execution Path
--------------

#. Receive Message from SQS

#. Acquire lock with ``redlock`` using ``message_id`` to enforce idempotency.

#. Look for handler
    #. Look for event in message attributes and its respective handler.
    #. Look for default handler
    #. Raise KeyError

#. If handler is found, execute!
    #. If executed without exception
        - delete message from SQS
    #. If executed and exception was raised
        - log error
