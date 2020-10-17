from typing import Optional, Iterator, Any, Callable

import botocore.exceptions
import functools

from inspect import isawaitable

from iniesta.log import error_logger, logger
from iniesta.sessions import BotoSession
from iniesta.sns import SNSMessage

from insanic.conf import settings
from insanic.exceptions import APIException


class SNSClient:
    """
    Initialize client with topic arn and endpoint url.

    :param topic_arn: If you would like to initialize this client with a
     different topic. Defaults to :code:`INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN` if not passed.
    :param region_name: Takes priority or defaults to :code:`INIESTA_SNS_REGION_NAME` settings.
    :param endpoint_url: Takes priority or defaults to :code:`INIESTA_SNS_ENDPOINT_URL` settings.
    """

    def __init__(
        self,
        topic_arn: Optional[str] = None,
        *,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):

        self.topic_arn = (
            topic_arn or settings.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN
        )
        self.region_name = region_name or BotoSession.aws_default_region
        self.endpoint_url = endpoint_url or settings.INIESTA_SNS_ENDPOINT_URL

    @classmethod
    async def initialize(
        cls,
        *,
        topic_arn: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        """
        Class method to initialize the SNS Client and confirm the topic exists.
        We needed to do this because of asyncio functionality

        :param topic_arn: If you would like to initialize this client with a
         different topic. Defaults to :code:`INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN` if not passed.
        :param region_name: Takes priority or defaults to :code:`BotoSession.aws.default_region` settings.
        :param endpoint_url: Takes priority or defaults to :code:`INIESTA_SNS_ENDPOINT_URL` settings.
        :return: An initialized instance of :code:`cls` (:code:`SQSClient`).
        :rtype: :code:`SNSClient`
        """

        topic_arn = topic_arn or settings.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN

        try:
            await cls._confirm_topic(
                topic_arn, region_name=region_name, endpoint_url=endpoint_url
            )
        except botocore.exceptions.ClientError as e:
            error_message = f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']} {topic_arn}"
            error_logger.critical(error_message)
            raise

        return cls(
            topic_arn, region_name=region_name, endpoint_url=endpoint_url
        )

    @classmethod
    async def _confirm_topic(
        cls,
        topic_arn: str,
        *,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ) -> None:
        """
        Confirm that the topic exists by request :code:`get_topic_attributes` to AWS.
        """
        session = BotoSession.get_session()

        async with session.create_client(
            "sns",
            region_name=region_name or BotoSession.aws_default_region,
            endpoint_url=endpoint_url or settings.INIESTA_SNS_ENDPOINT_URL,
            aws_access_key_id=BotoSession.aws_access_key_id,
            aws_secret_access_key=BotoSession.aws_secret_access_key,
        ) as client:
            await client.get_topic_attributes(TopicArn=topic_arn)

    async def _list_subscriptions_by_topic(self, next_token=None):
        session = BotoSession.get_session()

        query_args = {"TopicArn": self.topic_arn}

        if next_token is not None:
            query_args.update({"NextToken": next_token})

        try:
            async with session.create_client(
                "sns",
                region_name=BotoSession.aws_default_region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=BotoSession.aws_access_key_id,
                aws_secret_access_key=BotoSession.aws_secret_access_key,
            ) as client:
                return await client.list_subscriptions_by_topic(**query_args)
        except botocore.exceptions.ClientError as e:
            error_message = f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']} {self.topic_arn}"
            error_logger.critical(error_message)
            raise

    async def list_subscriptions_by_topic(self) -> Iterator:
        """
        The list of subscriptions attached to the current topic.

        The subscription object is in the following format.

        .. code-block:: json

            {
                "SubscriptionArn": "string",
                "Owner": "string",
                "Protocol": "string",
                "Endpoint": "string",
                "TopicArn": "string"
            }

        :return: list of subscriptions
        """

        next_token = True
        while next_token:
            _subscriptions = await self._list_subscriptions_by_topic(
                None if next_token is True else next_token
            )

            for _subscription in _subscriptions["Subscriptions"]:
                yield _subscription

            next_token = _subscriptions.get("NextToken")

    async def get_subscription_attributes(self, subscription_arn: str) -> dict:
        """
        Retrieves the attributes of the subscription from AWS.

        Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.get_subscription_attributes
        for more information.
        """

        async with BotoSession.get_session().create_client(
            "sns",
            region_name=BotoSession.aws_default_region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=BotoSession.aws_access_key_id,
            aws_secret_access_key=BotoSession.aws_secret_access_key,
        ) as client:
            return await client.get_subscription_attributes(
                SubscriptionArn=subscription_arn
            )

    def create_message(
        self,
        *,
        event: str,
        message: Any,
        version: int = 1,
        raw_event: bool = False,
        **message_attributes,
    ) -> SNSMessage:
        """
        A helper method to create a SNSMessage object.

        :param event: The event to publish (will be used to filter).
        :param message: The message body to send with event.
        :param version: A version to publish. Defaults to 1.
        :param message_attributes: Any attributes to include in the message.
            Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.publish.
        """
        message_payload = SNSMessage.create_message(
            self,
            event=event,
            message=message,
            version=version,
            raw_event=raw_event,
            **message_attributes,
        )
        return message_payload

    def publish_event(
        self, *, event: str, version: int = 1, **message_attributes
    ) -> Callable:
        """
        Used for decorating a view function or view class method.
        This publishes the message with the event specified with
        the return of the decorated function or method.
        This only triggers if the response is with a status code
        of less than 300.

        :param event: Event value to be published.
        :param version: The version.
        :param message_attributes: Any extra message_attributes to be attached to the event.
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
                        message = self.create_message(
                            event=event,
                            message=response.body.decode(),
                            version=version,
                            **message_attributes,
                        )
                        try:
                            await message.publish()
                        except Exception:
                            logger.exception(
                                "[INIESTA] Something when wrong when publishing. But continuing to serve."
                            )

                    return response

            return wrapped

        return wrapper
