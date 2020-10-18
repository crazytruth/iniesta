Event Polling Initialization
=============================

If your application need to receive events for consumption,
you should set your :code:`INIESTA_INITIALIZATION_TYPE`
to include :code:`EVENT_POLLING`.

Preparation
------------

-   All necessary AWS resources have been created

    - A SNS Topic
    - A SQS Queue
    - Subscription with filter policies
    - Proper permissions

-   :code:`EVENT_POLLING` is included in :code:`INIESTA_INITIALIZATION_TYPE`
-   Set :code:`INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN`
-   Set your :code:`INIESTA_SQS_CONSUMER_FILTERS`
-   Set your :code:`INIESTA_SQS_QUEUE_NAME` or fallback to
    :code:`INIESTA_SQS_QUEUE_NAME_TEMPLATE`.
-   Set your cache connection details on :code:`INIESTA_CACHES`
    that :code:`aioredlock` will use. It is recommended to have
    at least 3 different cache connections.


To get an idea of what AWS Resources are needed, please
refer to :doc:`aws_resources`.

Execution
---------

On initialization:

#.  Iniesta will verify the global topic arn defined
    in the settings exist. (e.g.
    the :code:`INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN` setting)
#.  Verify that filter policies exist on AWS.
    The :code:`INIESTA_SQS_CONSUMER_FILTERS`.
#.  Loads the iniesta settings to Insanic's settings
#.  Attaches the appropriate listeners.


Then on start up:

#.  Initializes the :code:`SQSClient` and sets it
    to :code:`app.messi`.
#.  Checks if the queue exists.
#.  Checks if the queue is subscribed to the topic.
#.  Checks if the necessary permissions exists.
#.  Starts polling the queue for messages.


Now, we should be able to receive message from the queue.
BUT, what do we do with those messages? We need to attach
handlers.


Handlers
---------

We need to attach handlers for each event.  :code:`SQSClient`
provides a class method to attach handlers to process the
received messages.

.. code-block:: python

    from iniesta.sqs import SQSClient

    @SQSClient.handler("SomethingHappened.somewhere")
    def something_happened_handler(message):
        # .. do some logic
        return


Or a class method.

.. code-block:: python

    class Handlers:
        @SQSClient.handler(['SomethingHappened.elsewhere', "AnotherEvent.knowhere"])
        def something_happened_handler(self, message):
            # .. some logic
            pass

Or directly.

.. code-block:: python

    def something_else_happened_handler(message):
        # do some logic
        return

    SQSClient.add_handler(something_else_happened_handler,
                          "SomethingElseHappened.nowhere")


Note that the callable must receive a :code:`message` argument.
Also the events can be a list if you want to bind the same
handler for multiple events.

To define a default handler, don't set a event. The default
handler is if Iniesta receives a message that doesn't have
an attached handler, it falls back to the default handler.

.. code-block:: python

    @SQSClient.handler
    def default_handler(message)
        # do something
        pass


Polling
--------

The typical flow for when Iniesta receives a message
is as follows.

#.  Receives message from SQS.
#.  Acquires a lock with :code:`aioredlock` using the
    :code:`message_id` to enforce idempotency.
#.  Once acquired, look for a handler:

    #.  Match the event in :code:`INIESTA_SNS_EVENT_KEY`
        in the received message body for a registered
        handler.
    #.  If not found, look for a default handler.
    #.  If not found, raise :code:`KeyError`.

#.  If a handler is found execute!

    #.  If executed, and no exception is raised, delete
        the message from sqs.
    #.  If exception is raises, do nothing so the
        message can be consumed again after the
        invisibility timeout.

.. note::

    There is currently a know issue where if the module
    containing the handlers are not imported on start up
    the handlers do not get registered.  For a quick
    fix import the module(s) where your Insanic app resides.


See Also
---------

- :ref:`api-iniesta-sqs-client` Reference
- :ref:`api-iniesta-sqs-message` Reference
- `aioredlock <https://github.com/joanvila/aioredlock>`_
