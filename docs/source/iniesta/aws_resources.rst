AWS Resources
==============

This is just a reference for the minimum requirements for
certain AWS Resources. Please modify for your purposes.

In this example we will be using botocore to create all
the necessary resources.

.. code-block:: python

    import botocore.session
    session = botocore.session.get_session()

    sqs = session.create_client('sqs')

    sns = session.create_client('sns')


1. A SNS Topic
---------------

No separate settings required for setting up a SNS Topic.

.. code-block:: python

    create_topic_response = sns.create_topic(Name='development-global')


2. A SQS Queue
---------------

No separate settings required for setting up a SQS Queue.

.. code-block:: python

    create_queue_response = sqs.create_queue(QueueName='iniesta-development-example')

    # to get your queue arn. We need this to subscribe later.
    queue_attributes = sqs.get_queue_attributes(
        QueueUrl=create_queue_response["QueueUrl"], AttributeNames=["QueueArn"]
    )

3. Subscribe SQS to SNS
------------------------

Make sure you get your filter policies.

.. code-block:: python

    # as an example if
    filter_policy = {
            "iniesta_pass": [
                "hello.iniesta",
                {"prefix": "Request."},
            ]
        }

    subscribe_response = sns.subscribe(
            TopicArn=create_topic_response["TopicArn"],
            Protocol="sqs",
            Endpoint=queue_attributes["Attributes"]["QueueArn"],
            Attributes={
                "FilterPolicy": json.dumps(filter_policy),
                "RawMessageDelivery": "true",
            },
        )


4. Set up permissions
----------------------

.. code-block:: python

    response = sqs.set_queue_attributes(
                QueueUrl=create_queue_response["QueueUrl"],
                Attributes={
                    "Policy": json.dumps(
                        {
                            "Version": "2012-10-17",
                            "Id": f"{queue_attributes['Attributes']['QueueArn']}/SQSDefaultPolicy",
                            "Statement": [
                                {
                                    "Sid": "Sid1552456721343",
                                    "Effect": "Allow",
                                    "Principal": "*",
                                    "Action": "SQS:SendMessage",
                                    "Resource": queue_attributes["Attributes"][
                                        "QueueArn"
                                    ],
                                    "Condition": {
                                        "ArnEquals": {
                                            "aws:SourceArn": create_topic_response[
                                                "TopicArn"
                                            ]
                                        }
                                    },
                                }
                            ],
                        }
                    )
                },
            )


5. Run
------

You should be able to run :code:`EVENT_POLLING` with these resources created.
