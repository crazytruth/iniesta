Iniesta
========

Welcome to Iniesta's Documentation.  Iniesta is a extension
for `Insanic <https://github.com/crazytruth/insanic>`_ that
provides messaging integration for implementing a event
driven architecture pattern.  The basic run down of
what it does is that it publishes messages to
AWS SNS and also can poll AWS SQS for events to consume.


Background
----------

This project's inception was when I was working for my
former employer. The service was running on fully
functioning microservice architecture but found some
inefficiencies with some REST APIs. Some would need to call
as much as 10+ other services and to provide context, if
any of them failed, that single API would error.
Even with non critical requests to other services,
would sometimes fail which would result in data
inconsistencies.  We were trying to enforce strong
data consistency even when it was not needed.

To alleviate this issue, integration of a event driven
system was required. To rapidly migrate portions of non
critical communications and to reduce time for
developers needing to learn how to use AWS SNS and SQS,
Iniesta was born.

You might ask what or why is Iniesta? Andrés Iniesta is
a Spanish professional soccer player who plays as a
central midfielder. He is considered one the best soccer
players and one of the greatest midfielders of all time.
For those of you unfamiliar with soccer, a midfielder is
responsible for playmaking and passing the
soccer ball from the defense to the forwards.

Consequently, this project aims to be the messenger
between services; a proxy, for sending
messages(the soccer ball) from the producers(defenders)
to the consumer(strikers) albeit the messages fan out
and there is only one soccer ball.

Iniesta was decided upon after a long grueling
discussion, because everyone knows that variable
naming is the most strenuous.

Since it's initial internal release, it has been modified to be
as flexible as possible when communicating with AWS.


Features
---------

- Asynchronous message handling.
- Produce messages to a global SNS Topic.
- Filters for verification and subscribing SQS to SNS.
- Polling for SQS and receiving messages.
- Decorator for consuming messages with defined parameters.
- Locks for idempotent message handling.
- Checks for if proper subscriptions have been setup.
- Verifications on proper permissions.
- Decorators for emitting messages.


Good to Know
-------------

Because Iniesta integrates AWS SNS and AWS SQS, a basic
working knowledge of each of those technologies would be
of great help.

Refer to `AWS SNS Documentation <https://docs.aws.amazon.com/sns/latest/dg/welcome.html>`_
and `AWS SQS Documentation <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html>`_
to catch up on those.

Also background knowledge of a distributed event driven system
will be of help!
