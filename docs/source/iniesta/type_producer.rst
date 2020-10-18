Producer Initialization
========================

If your application produces events for other application
to consume, you should set your :code:`INIESTA_INITIALIZATION_TYPE`
to include :code:`SNS_PRODUCER`.

On start up of Insanic, a :code:`SNSClient` instance is created and
attached to the application.  It is accessible with :code:`app.xavi`.
It is recommended to have only one :code:`SNSClient` for each
topic until the server is stopped.  For other topics, you will need to
create a separate :code:`SNSClient` and manage its lifecycle.


Publishing Messages
--------------------

With our client initialized, we can now create a :code:`SNSMessage` to
publish to our topic.  There are several ways we can do this.
We can to either publish messages explicitly or decorate view functions or methods to
publish events on successful execution.


With :code:`SNSClient`
^^^^^^^^^^^^^^^^^^^^^^

The :code:`SNSClient` provides a factory method
to create a :code:`SNSMessage` to prepare and send.

.. code-block:: python

    async def publish_somewhere(app):

        message: SNSMessage = app.xavi.create_message(
            event="SomeEvent",
            message={"extra": "extra stuff i want to send"}
        )

        await message.publish()


With :code:`SNSMessage`
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from iniesta.sns import SNSMessage

    async def somewhere_in_my_code(app):

        message = SNSMessage.create_message(
            client=app.xavi,
            event="SomeEvent",
            message={"extra": "extra stuff I want to send"}
        )

        await message.publish()


With a decorator
^^^^^^^^^^^^^^^^^

The client also provides a separate decorator that can
simplify event publishing.

.. code-block:: python

    from sanic.response import json
    from insanic.views import InsanicView
    from . import app # your Insanic app

    class MyPublishingView(InsanicView):

        @app.xavi.publish_event(event="SaidHello")
        async def post(self, request, *args, **kwargs):

            return json({"hello": "hi"})

    app.add_route(MyPublishingView.as_view(), "/hi")

Now if we run our server, and call the :code:`/hi` endpoint,
an event will be published with the event :code:`SaidHello`,
with the response body as the message.

.. note::

    Publishing will only trigger if the response has a status_code
    of less than 300. Any exceptions raised or a response with
    a explicit status code of more than 300 will NOT publish
    a message.


Initializing a SNSClient
-------------------------

If you have more than 1 topic that you need to publish to,
we can create a separate client to connect to.

To create your own :code:`SNSClient` we need to use a separate
async class method to initialize our client.

.. code-block:: python

    from iniesta.sns import SNSClient

    async def initialize_client():
        client = await SNSClient.initialize(
            topic_arn = "your topic arn"
        )

This will confirm the topic exists and return an initialized
:code:`SNSClient` instance.  It is not recommended creating
a :code:`SNSClient` each time your need to publish a message
so, you will need to manage its lifecycle.  A possible approach
is to initialize on the before start listeners and attach
it to the application.


See Also
---------

- :ref:`api-iniesta-sns-client`
- :ref:`api-iniesta-sns-message`
