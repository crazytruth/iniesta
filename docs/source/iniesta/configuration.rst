Configuration
==============

Iniesta provides an extensive list of
configurations for its behavior.  All
Iniesta settings are prefixed with
:code:`INIESTA` and are loaded into Insanic's
settings on initialization.

Important Configurations
-------------------------

If you have read through the :doc:`Getting Started <getting_started>`
documentation, there are some mandatory configurations for Iniesta
to function properly.

:code:`INIESTA_INITIALIZATION_TYPE`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is arguably the most important as it determines how
Iniesta will be running. The value should be a tuple of strings
with the values being:

- :code:`SNS_PRODUCER`
- :code:`EVENT_POLLING`
- :code:`QUEUE_POLLING`
- :code:`CUSTOM`

A combination of the above values can be set and
Iniesta will run accordingly.  More information is provided
in their respective initialization type documentations.

-   :doc:`type_event_polling`
-   :doc:`type_producer`
-   :doc:`type_queue_polling`
-   :doc:`type_custom`


:code:`INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have initialized Iniesta with either :code:`SNS_PRODUCER` and/or
:code:`EVENT_POLLING`, this value becomes required.

When "publishing" messages, Iniesta needs the topic arn to publish
its messages to.

When polling for *events*, Iniesta needs it to verify that all the
necessary AWS resources and permissions have been created.

:code:`INIESTA_SQS_CONSUMER_FILTERS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the list of events that Iniesta should be expecting.
It should be a list of strings that represent the events.

Some examples could be:

- :code:`"UserCreated.user"`: To only receive the literal event.
- :code:`"PostCreated.*"`: To receive all :code:`PostCreated` events regardless of who produced it.

Because of AWS filter policy restrictions, only prefixes can be filtered for.
Currently Iniesta only provides values for exact matching or prefix filtering.

For more information view the `AWS Filter Policy Documentation <https://docs.aws.amazon.com/sns/latest/dg/sns-subscription-filter-policies.html>`_
for more information.


:code:`INIESTA_SNS_EVENT_KEY`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the string value of the key of the event.  This is
essentially the key that is set in the filter policies, with the
event as the value.


:code:`INIESTA_SQS_QUEUE_NAME`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The default SQS queue that Iniesta should be polling. If not
set it fallbacks to :code:`INIESTA_SQS_QUEUE_NAME_TEMPLATE`,
where the templates is :code:`iniesta-{env}-{service_name}`
(e.g. :code:`iniesta-development-user`).


AWS Configurations
-------------------

There are 3 configs that will need to be set for Iniesta to
communicate with AWS APIs.

- :code:`AWS_ACCESS_KEY_ID`
- :code:`AWS_SECRET_ACCESS_KEY`
- :code:`AWS_DEFAULT_REGION`

If for example you have separate access keys and secrets from
the default you can prefix :code:`INIESTA_` and Iniesta will
take those over the ones without the prefix.

Value Priority
^^^^^^^^^^^^^^^

1. :code:`AWS_*` from the environment.
2. :code:`INIESTA_AWS_*` from Insanic's settings.
3. :code:`AWS_*` from Insanic's settings.

The loaded variables can be access from
:code:`iniesta.sessions.BotoSession`.  These are the values
that Iniesta uses through the package.


Configuration Reference
------------------------

.. automodule:: iniesta.config
    :members:
