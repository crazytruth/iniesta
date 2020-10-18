Queue Polling Initialization
=============================

Queue Polling is when you just want to poll a queue and
is not concerned with event driven approach.

To set this:

Preparation
------------

-   Have an AWS SQS queue created for your application.
-   Have :code:`QUEUE_POLLING` in your
    :code:`INIESTA_INITIALIZATION_TYPE` settings.
-   Have your :code:`INIESTA_SQS_QUEUE_NAME` set to the
    name of your queue or have your queue name in the
    format of :code:`INIESTA_SQS_QUEUE_NAME_TEMPLATE`.
-   Have your redis connection details in :code:`INIESTA_CACHES`.

Execution
---------

On initialization the following happens:

#.  Loads iniesta configs
#.  Attaches necessary listeners

Then when run:

#.  Initializes a :code:`SQSClient` on :code:`app.messi`.
#.  Starts Polling for messages.

Handlers
---------

When receiving messages, unlike event polling, we need to
set up a single default handler for queue polling.

.. code-block:: python

    @SQSClient.handler
    def default_handler(message)
        # do something
        pass

.. note::

    Like with event polling handlers, there is currently
    a know issue where if the module containing the
    handlers are not imported on start up
    the handlers do not get registered.  For a quick
    fix import the module(s) where your Insanic app resides.

See Also
--------

- :ref:`api-iniesta-sqs-client` Reference
- :ref:`api-iniesta-sqs-message` Reference
- `aioredlock <https://github.com/joanvila/aioredlock>`_
