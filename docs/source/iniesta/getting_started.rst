Getting Started
================

Prerequisites
-------------

#.  Iniesta is an extension for Insanic, therefore requires
    :code:`asyncio`, available in python version 3.6 and up.

#.  Since Iniesta interacts with AWS SNS and SQS, we need
    AWS credentials for Iniesta to work properly.

#.  Confirm you have your AWS SNS topic created.

#.  Confirm you have your AWS SQS for the service created.

#.  Confirm you have your subscriptions registered for your topic and queue.

#.  Confirm you have the necessary permissions for your queue so that the topic can send messages to the queue.

.. note::

    Certain AWS resources may not be needed depending on the initialization type.

For information on how to create the necessary resources
in AWS, please refer to the respective AWS Documentation.

Refer to :doc:`aws_resources` for minimum AWS configuration
requirements for Iniesta.

Installing
-----------

.. code-block:: sh

    pip install insanic-iniesta

Initialization
---------------

Before initialization of Iniesta, we need to define
:code:`INIESTA_INITIALIZATION_TYPE` in our config.

.. code-block:: python

    # for our example in config.py
    INIESTA_INITIALIZATION_TYPE = ['EVENT_POLLING']
    INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN = "your global topic arn"
    INIESTA_SQS_CONSUMER_FILTERS = ["SomeEvent"]


Now, at the location where we have instantiated :code:`Insanic` (e.g. usually :code:`app.py`).

.. code-block:: python

    from insanic import Insanic
    from insanic.conf import settings
    from iniesta import Iniesta

    from . import config

    __version__ = "0.1.0.dev0"

    settings.configure(config)
    app = Insanic('example',  version=__version__)

    Iniesta.init_app(app)


You should now be able to run your Insanic application.


Installation for :code:`iniesta` commands
------------------------------------------

We need some extra packages to run the commands.

.. code-block:: text

    pip install iniesta[cli]
