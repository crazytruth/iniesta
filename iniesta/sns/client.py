import botocore.exceptions
import functools

from inspect import isawaitable

from iniesta.sessions import BotoSession
from iniesta.sns import SNSMessage

from insanic.conf import settings
from insanic.exceptions import APIException
from insanic.log import error_logger, logger


class SNSClient:

    def __init__(self, topic_arn=None):
        """
        initialize client with topic arn and endpoint url

        :param topic_arn:
        """
        self.topic_arn = topic_arn or settings.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN
        self.region_name = settings.INIESTA_SNS_REGION_NAME
        self.endpoint_url = settings.INIESTA_SNS_ENDPOINT_URL

    @classmethod
    async def initialize(cls, *, topic_arn):
        """
        Class method to initialize the SNS Client and confirm the topic exists.
        We needed to do this because of asyncio functionality

        :param topic_arn:
        :return:
        """

        try:
            await cls._confirm_topic(topic_arn)
        except botocore.exceptions.ClientError as e:
            error_message = f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']} {topic_arn}"
            error_logger.critical(error_message)
            raise

        return cls(topic_arn)

    @classmethod
    async def _confirm_topic(cls, topic_arn):
        """
        Confirm that the topic exists

        :param topic_arn:
        :return:
        """
        session = BotoSession.get_session()

        async with session.create_client('sns', region_name=settings.INIESTA_SNS_REGION_NAME,
                                         endpoint_url=settings.INIESTA_SNS_ENDPOINT_URL,
                                         aws_access_key_id=BotoSession.aws_access_key_id,
                                         aws_secret_access_key=BotoSession.aws_secret_access_key) as client:
            await client.get_topic_attributes(TopicArn=topic_arn)

    async def _list_subscriptions_by_topic(self, next_token=None):
        session = BotoSession.get_session()

        query_args = {"TopicArn": self.topic_arn}

        if next_token is not None:
            query_args.update({"NextToken": next_token})

        try:
            async with session.create_client('sns', region_name=self.region_name, endpoint_url=self.endpoint_url,
                                             aws_access_key_id=BotoSession.aws_access_key_id,
                                             aws_secret_access_key=BotoSession.aws_secret_access_key) as client:
                return await client.list_subscriptions_by_topic(**query_args)
        except botocore.exceptions.ClientError as e:
            error_message = f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']} {self.topic_arn}"
            error_logger.critical(error_message)
            raise

    async def list_subscriptions_by_topic(self):
        """
        Subscription:
        {
            'SubscriptionArn': 'string',
            'Owner': 'string',
            'Protocol': 'string',
            'Endpoint': 'string',
            'TopicArn': 'string'
        }

        :return: list of subscriptions
        """

        next_token = True
        while next_token:
            _subscriptions = await self._list_subscriptions_by_topic(None if next_token is True else next_token)

            for _subscription in _subscriptions['Subscriptions']:
                yield _subscription

            next_token = _subscriptions.get('NextToken')

    async def get_subscription_attributes(self, subscription_arn):

        async with BotoSession.get_session().create_client(
                'sns', region_name=self.region_name, endpoint_url=self.endpoint_url,
                aws_access_key_id=BotoSession.aws_access_key_id,
                aws_secret_access_key=BotoSession.aws_secret_access_key) as client:
            return await client.get_subscription_attributes(SubscriptionArn=subscription_arn)

    def create_message(self, *, event, message, version=1, **message_attributes):
        """

        :param event: the event to publish (will be used to filter)
        :param message: message to send with event
        :param version: a version to publish
        :param message_attributes:
        :return:
        """
        message_payload = SNSMessage.create_message(self, event=event,
                                                    message=message,
                                                    version=version,
                                                    **message_attributes)
        return message_payload

    def publish_event(self, *, event, version=1, **message_attributes):
        """
        decorator for publishing event with event specified in decorator and publishes
        the return of the decorated function. Can only be used on views.

        :param event: Event name to be published
        :param version: The version.
        :param message_attributes: Any extra message_attributes to be attached to the event
        :return:
        """


        def wrapper(func):

            @functools.wraps(func)
            async def wrapped(*args, **kwargs):

                try:
                    response = func(*args, **kwargs)
                except APIException:
                    raise
                except Exception:
                    raise
                else:
                    if isawaitable(response):
                        response = await response

                    if response.status < 300:
                        message = self.create_message(event=event, message=response.body.decode(),
                                                      version=version, **message_attributes)
                        try:
                            await message.publish()
                        except Exception as e:
                            logger.exception("[INIESTA] Something when wrong when publishing. But continuing to serve.")

                    return response
            return wrapped
        return wrapper

