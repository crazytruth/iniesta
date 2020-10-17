import asyncio
from typing import Optional, Callable, Any, Union

import botocore.exceptions
import ujson as json

from aioredlock import Aioredlock, LockError
from inspect import signature, isawaitable, isfunction
from insanic.conf import settings
from insanic.exceptions import ImproperlyConfigured

# from insanic.log import logger, error_logger

from iniesta.exceptions import StopPolling
from iniesta.log import logger, error_logger
from iniesta.sessions import BotoSession
from iniesta.sns import SNSClient
from iniesta.utils import filter_list_to_filter_policies

from .message import SQSMessage


default = object()


class SQSClient:

    endpoint_url = None
    lock_key = "sqs:event:{message_id}"

    handlers = {}  # dict with {event: handler function}
    queue_urls = {}  # dict with {queue_name: queue_url}

    def __init__(
        self,
        *,
        queue_name: str = None,
        endpoint_url: str = None,
        region_name: str = None,
        retry_count: int = None,
        lock_timeout: int = None,
    ):
        """
        Initializes a SQSClient instance

        :param queue_name:  If None, defaults to INIESTA_SQS_QUEUE_NAME_TEMPLATE
        :param retry_count: retry count for aioredlock, defaults to ``INIESTA_LOCK_RETRY_COUNT``
        :param lock_timeout: lock timeout for aioredlock. Defaults to ``INIESTA_LOCK_TIMEOUT``

        :raise KeyError: If application was not initialized with one of the initialization methods.
        """
        self.queue_name = (
            self.default_queue_name() if queue_name is None else queue_name
        )
        self.region_name = region_name or BotoSession.aws_default_region
        try:
            self.queue_url = self.queue_urls[self.queue_name]
        except KeyError:
            error_logger.error(
                f"Please use initialize to initialize queue: {queue_name}"
            )
            raise

        self.endpoint_url = endpoint_url or getattr(
            settings, "INIESTA_SQS_ENDPOINT_URL", None
        )
        self._filters = None

        retry_count = retry_count or settings.INIESTA_LOCK_RETRY_COUNT
        lock_timeout = lock_timeout or settings.INIESTA_LOCK_TIMEOUT

        # TODO: get connection info from insanic get connection
        connections = []
        for cache_name, conn_info in settings.INSANIC_CACHES.items():
            if cache_name.startswith("iniesta"):
                connections.append(
                    "redis://{HOST}:{PORT}/{DATABASE}".format(**conn_info)
                )

        self.lock_manager = Aioredlock(
            connections,
            retry_count=retry_count,
            internal_lock_timeout=lock_timeout,
        )

    @classmethod
    def default_queue_name(cls) -> str:
        return (
            settings.INIESTA_SQS_QUEUE_NAME
            or settings.INIESTA_SQS_QUEUE_NAME_TEMPLATE.format(
                env=settings.ENVIRONMENT, service_name=settings.SERVICE_NAME
            )
        )

    @classmethod
    async def initialize(
        cls,
        *,
        queue_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
    ):
        """
        The initialization classmethod that should be first run before any subsequent SQSClient initializations.

        :param queue_name: queue_name if want to initialize client with a different queue
        :rtype: :code:`SQSClient`
        """
        session = BotoSession.get_session()

        endpoint_url = endpoint_url or getattr(
            settings, "INIESTA_SQS_ENDPOINT_URL", None
        )

        if queue_name is None:
            queue_name = cls.default_queue_name()

        # check if queue exists
        if queue_name not in cls.queue_urls:
            try:
                async with session.create_client(
                    "sqs",
                    region_name=region_name or BotoSession.aws_default_region,
                    endpoint_url=endpoint_url,
                    aws_access_key_id=BotoSession.aws_access_key_id,
                    aws_secret_access_key=BotoSession.aws_secret_access_key,
                ) as client:
                    response = await client.get_queue_url(QueueName=queue_name)
            except botocore.exceptions.ClientError as e:
                error_message = f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']} {queue_name}"
                error_logger.critical(error_message)
                raise
            else:
                queue_url = response["QueueUrl"]
                cls.queue_urls.update({queue_name: queue_url})

        sqs_client = cls(queue_name=queue_name)

        # check if subscription exists
        # await cls._confirm_subscription(sqs_client, topic_arn, endpoint_url)

        return sqs_client

    async def confirm_subscription(self, topic_arn: str) -> None:
        """
        Confirms the correct subscriptions are in place in AWS SNS

        :param topic_arn: Topic to check subscriptions for.
        :raises EnvironmentError: If the the queue is not found.
        :raises AssertionError: If the registered filters on AWS do not match current config filters.
        """

        sns_client = SNSClient(topic_arn)
        subscriptions = sns_client.list_subscriptions_by_topic()
        subscription_list = []
        async for subs in subscriptions:
            subscription_list.append(subs)
            if self.queue_name in subs.get("Endpoint", "").split(":"):
                service_subscriptions = subs
                break
        else:
            raise EnvironmentError(
                f"Unable to find subscription for {settings.SERVICE_NAME}"
            )

        if settings.INIESTA_ASSERT_FILTER_POLICIES:
            # check if filters match specified
            subscription_attributes = await sns_client.get_subscription_attributes(
                subscription_arn=service_subscriptions["SubscriptionArn"]
            )

            filter_policies = json.loads(
                subscription_attributes["Attributes"].get("FilterPolicy", "{}")
            )

            if filter_policies != self.filters:
                raise AssertionError(
                    f"Subscription filters and current filters are not equivalent. "
                    f"{filter_policies} {self.filters}"
                )

    async def confirm_permission(self) -> None:
        """
        Confirms correct permissions are in place.

        :raises ImproperlyConfigured: If the permissions were not found.
        :raises AssertionError: If the permissions are not correctly configured on AWS.
        """
        session = BotoSession.get_session()
        async with session.create_client(
            "sqs",
            region_name=self.region_name or BotoSession.aws_default_region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=BotoSession.aws_access_key_id,
            aws_secret_access_key=BotoSession.aws_secret_access_key,
        ) as client:
            policy_attributes = await client.get_queue_attributes(
                QueueUrl=self.queue_url, AttributeNames=["Policy"]
            )

        try:
            policies = json.loads(policy_attributes["Attributes"]["Policy"])
            statement = policies["Statement"][0]
        except KeyError:
            raise ImproperlyConfigured("Permissions not found.")

        # need "Effect": "Allow", "Action": "SQS:SendMessage"
        assert statement["Effect"] == "Allow"
        assert "SQS:SendMessage" in statement["Action"]
        # assert statement['Condition']['ArnEquals']['aws:SourceArn'] == topic_arn

    @property
    def filters(self) -> dict:
        if self._filters is None:
            self._filters = filter_list_to_filter_policies(
                settings.INIESTA_SNS_EVENT_KEY,
                settings.INIESTA_SQS_CONSUMER_FILTERS,
            )
        return self._filters

    def start_receiving_messages(self, loop=None) -> None:
        """
        Method to start polling for messages.
        """
        self._receive_messages = True

        if loop is None:
            loop = asyncio.get_event_loop()

        self._polling_task = asyncio.ensure_future(self._poll())
        self._loop = loop

    async def stop_receiving_messages(self) -> None:
        """
        Method to stop polling
        """
        self._receive_messages = False
        await self.lock_manager.destroy()
        self._polling_task.cancel()

    async def handle_message(self, message: SQSMessage) -> tuple:
        """
        Method that hold logic to handle a certain type of mesage

        :param message: Message to handle
        :raises LockError: If lock could not be acquired for the message
        :raises Exception: General exception handler attaches the message and message handler
        :return: Returns a tuple of the message and result of the handler
        """
        lock = None

        try:
            lock = await self.lock_manager.lock(
                self.lock_key.format(message_id=message.message_id)
            )
            if not lock.valid:
                raise LockError(
                    f"Could not acquire lock for {message.message_id}"
                )

            if message.event in self.handlers:
                handler = self.handlers[message.event]
            elif default in self.handlers:
                handler = self.handlers[default]
            else:
                raise KeyError(f"{message.event} handler not found!")

        except Exception as e:
            e.message = message
            e.handler = None
            raise e
        else:
            try:
                result = handler(message)
                if isawaitable(result):
                    result = await result

                return message, result
            except Exception as e:
                e.message = message
                e.handler = handler
                raise e
        finally:
            if lock:
                await self.lock_manager.unlock(lock)

    def handle_error(self, exc: Exception) -> None:
        """
        If an exception occured while handling the message, log the error.
        """

        message = exc.message
        handler = getattr(exc, "handler", None)

        extra = {
            "iniesta_pass": message.event,
            "sqs_message_id": message.message_id,
            "sqs_receipt_handle": message.receipt_handle,
            "sqs_md5_of_body": message.md5_of_body,
            "sqs_message_body": message.raw_body,
            "sqs_attributes": json.dumps(message.attributes),
            "handler_name": handler.__qualname__ if handler else None,
        }

        error_logger.critical(
            f"[INIESTA] Error while handling message: {str(exc)}",
            exc_info=exc,
            extra=extra,
        )

    async def handle_success(self, client, message: SQSMessage) -> dict:
        """
        Success handler for a message. Deletes the message from SQS.

        :param client: aws sqs client
        :return: Returns the response of the delete_message request.
        """

        message_id = message.message_id
        # if success must delete message from sqs
        logger.info(
            f"[INIESTA] Message handled successfully: msg_id={message_id}",
            extra={"sqs_message_id": message_id},
        )
        resp = await client.delete_message(
            QueueUrl=self.queue_url, ReceiptHandle=message.receipt_handle
        )
        logger.debug(
            f"[INIESTA] Message deleted: msg_id={message_id} "
            f"receipt_handle={message.receipt_handle}",
            extra={"sqs_message_id": message_id},
        )
        return resp

    async def _poll(self) -> str:
        """
        The long running method that consistently polls the SQS queue for
        messages.
        :return:
        """
        session = BotoSession.get_session()

        async with session.create_client(
            "sqs",
            region_name=self.region_name,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=BotoSession.aws_access_key_id,
            aws_secret_access_key=BotoSession.aws_secret_access_key,
        ) as client:
            try:
                while self._loop.is_running() and self._receive_messages:
                    try:
                        response = await client.receive_message(
                            QueueUrl=self.queue_url,
                            MaxNumberOfMessages=settings.INIESTA_SQS_RECEIVE_MESSAGE_MAX_NUMBER_OF_MESSAGES,
                            WaitTimeSeconds=settings.INIESTA_SQS_RECEIVE_MESSAGE_WAIT_TIME_SECONDS,
                            AttributeNames=["All"],
                            MessageAttributeNames=["All"],
                        )
                    except botocore.exceptions.ClientError as e:
                        error_logger.critical(
                            f"[INIESTA] [{e.response['Error']['Code']}]: {e.response['Error']['Message']}"
                        )
                    else:
                        event_tasks = [
                            asyncio.ensure_future(
                                self.handle_message(
                                    SQSMessage.from_sqs(client, message)
                                )
                            )
                            for message in response.get("Messages", [])
                        ]

                        for fut in asyncio.as_completed(event_tasks):
                            # NOTE: must catch CancelledError and raise
                            try:
                                message_obj, result = await fut
                            except asyncio.CancelledError:
                                raise
                            except Exception as e:
                                # if error log failure and pass so sqs message persists and message becomes visible again
                                self.handle_error(e)
                            else:
                                await self.handle_success(client, message_obj)

                        await self.hook_post_receive_message_handler()
            except asyncio.CancelledError:
                logger.info("[INIESTA] POLLING TASK CANCELLED")
                return "Cancelled"
            except StopPolling:
                # mainly used for tests
                logger.info("[INIESTA] STOP POLLING")
                return "Stopped"
            except Exception:
                if self._receive_messages and self._loop.is_running():
                    error_logger.critical("[INIESTA] POLLING TASK RESTARTING")
                    self._polling_task = asyncio.ensure_future(self._poll())
                error_logger.exception("[INIESTA] POLLING EXCEPTION CAUGHT")
            finally:
                await client.close()

        return "Shutdown"  # pragma: no cover

    @classmethod
    def handler(
        cls, event: Union[Callable, str, list, tuple] = None
    ) -> Callable:
        """
        Decorator for attaching a message handler for an event or if None, a default handler.
        """

        if event and isfunction(event):
            cls.add_handler(event, default)
            return event
        else:

            def register_handler(func):
                cls.add_handler(func, default if event is None else event)
                return func

            return register_handler

    @classmethod
    def add_handler(
        cls, handler: Callable, event: Union[str, list, tuple] = default
    ) -> None:
        """
        Method for manually declaring a handler for event(s).

        :param handler: A function to execute
        :param event: The event(or a list of event) the function is attached to.
        """
        cls._validate_handler_signature(handler)

        if isinstance(event, list) or isinstance(event, tuple):
            cls._validate_event_iterable(event)
            for e in event:
                cls._add_handler(handler, e)
        else:
            cls._validate_event_name(event)
            cls._add_handler(handler, event)

    @classmethod
    def _validate_event_iterable(cls, events):
        if len(set(events)) != len(events):
            raise ValueError("Duplication found in list of event")
        for e in events:
            cls._validate_event_name(e)

    @classmethod
    def _validate_event_name(cls, event):
        if event in cls.handlers.keys():
            raise ValueError(f"Handler for event [{event}] already exists.")

    @classmethod
    def _validate_handler_signature(cls, handler):
        args = signature(handler).parameters

        if not args:
            raise ValueError(
                f"Required parameter `message` missing "
                f"in the {handler.__name__}() route?"
            )

    @classmethod
    def _add_handler(cls, handler, event):
        cls.handlers.update({event: handler})

    async def hook_post_receive_message_handler(self):  # pragma: no cover
        pass

    def create_message(self, message: Any) -> SQSMessage:
        """
        A helper method to create an SQSMessage

        :param message: The message body. A json encodable object.
        """
        if not isinstance(message, str):
            message = json.dumps(message)

        return SQSMessage(self, message)
