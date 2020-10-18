Custom Initialization
=====================

Custom Initialization is where you don't want to Iniesta to
do anything and would like to set everything up your self.
By settings :code:`CUSTOM` in your
:code:`INIESTA_INITIALIZATION_TYPE`, Iniesta, only loads the
configs and you must create all the SNS and SQS Clients yourself,
as well as managing the lifecycle of the clients.


Polling Custom Queue
---------------------

First we need to create a custom :code:`SQSClient` and start
polling in the listeners.

1. Initialize and instantiate a :code:`SQSClient` in listener and start polling

.. code-block:: python

    # listeners.py
    from iniesta.sqs import SQSClient

    async def after_server_start_start_polling(app, loop, **kwargs):
        app.sqs_client = await SQSClient.initialize(queue_name="my_custom_queue")
        app.sqs_client.start_receiving_messages()

    # remember to stop before stopping server
    async def before_server_stop_stop_polling(app, loop, **kwargs):
        await app.sqs_client.stop_receiving_messages()

2. Attach the listeners to Insanic application

.. code-block:: python

    # app.py
    from insanic import Insanic
    from iniesta import Iniesta

    app = Insanic("my_service")
    Iniesta.init_app(app)

    from .listeners import after_server_start_start_polling, before_server_stop_stop_polling

    app.register_listener(after_server_start_start_polling, 'after_server_start')
    app.register_listener(before_server_stop_stop_polling, 'before_server_stop')

3. Create handlers and attach to custom :code:`SQSClient`

.. code-block:: python

    # handlers.py
    from iniesta.sqs import SQSClient

    client = SQSClient('my_custom_queue')

    @client.handler()
    def handle_something(message):
        # do some stuff
        return None


4. Run

Publishing to Custom SNS
-------------------------

All we need to create a custom :code:`SNSClient` and initialize it.

1. Initialize :code:`SNSClient`

.. code-block:: python

    # listeners.py
    from iniesta.sns import SNSClient

    async def after_server_start_initialize_sns(app, loop=None, **kwargs):
        app.sns_client = await SNSClient.initialize(
            topic_arn="my:custom:topic:arn"
        )

2. Attach listener to insanic app

.. code-block:: python

    # app.py
    from insanic import Insanic
    from iniesta import Iniesta

    app = Insanic("service")
    Iniesta.init_app(app)

    from .listeners import after_server_start_initialize_sns

    app.register_listener(after_server_start_initialize_sns, 'after_server_start')

3. Run!

4. Produce message anywhere in code

.. code-block:: python

    # somewhere.py maybe views.py
    from insanic.views import InsanicView
    from sanic.response import json

    from iniesta.sns import SNSClient


    class SomeView(InsanicView):

        async def get(self, request, *args, **kwargs);
            # ... do some stuff

            message = request.app.sns_client.create_message("MyCustomEvent", {"command": "formation"})
            await message.publish()

            return json({}, status=200)
