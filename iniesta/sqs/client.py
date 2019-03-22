import asyncio
import botocore.exceptions
import ujson as json

from aioredlock import Aioredlock, LockError
from inspect import signature, isawaitable
from insanic.conf import settings
from insanic.log import logger, error_logger

from iniesta.exceptions import StopPolling
from iniesta.sessions import BotoSession
from iniesta.sns import SNSClient

from .message import SQSMessage




class SQSClient:

    endpoint_url = None
    lock_key = "sqs:event:{message_id}"

    handlers = {} # dict with {event: handler function}
    queue_urls = {} # dict with {queue_name: queue_url}

    def __init__(self, queue_name, *, retry_count=None, lock_timeout=None, endpoint_url=None):
        self.queue_name = queue_name
        self.queue_url = self.queue_urls[queue_name]
        self.endpoint_url = endpoint_url
        self._filters = None

        retry_count = retry_count or settings.INIESTA_LOCK_RETRY_COUNT
        lock_timeout = lock_timeout or settings.INIESTA_LOCK_TIMEOUT

        # TODO: get connection info from insanic get connection
        self.lock_manager = Aioredlock(
            [
                {"host": settings.REDIS_HOST, "port": settings.REDIS_PORT, "db": settings.REDIS_DB}
            ],
            retry_count=retry_count,
            lock_timeout=lock_timeout
        )

    @classmethod
    async def initialize(cls, *, queue_name, endpoint_url=None):
        """
        the sns topic this queue is subscribed to

        :param sns_client:
        :param queue_name:
        :param endpoint_url:
        :return:
        """
        session = BotoSession.get_session()

        # check if queue exists
        if queue_name not in cls.queue_urls:
            try:
                async with session.create_client('sqs', endpoint_url=endpoint_url) as client:
                    response = await client.get_queue_url(QueueName=queue_name)
            except botocore.exceptions.ClientError as e:
                error_message = f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']} {queue_name}"
                error_logger.critical(error_message)
                raise
            else:
                queue_url = response['QueueUrl']
                cls.queue_urls.update({queue_name: queue_url})

        sqs_client = cls(queue_name, endpoint_url=endpoint_url)

        # check if subscription exists
        # await cls._confirm_subscription(sqs_client, topic_arn, endpoint_url)

        return sqs_client

    async def confirm_subscription(self, sns_client):

        async for subs in sns_client.list_subscriptions_by_topic():
            if self.queue_name in subs.get('Endpoint', "").split(":"):
                service_subscriptions = subs
                break
        else:
            raise EnvironmentError(f"Unable to find subscription for {settings.SERVICE_NAME}")

        # check if filters match specified
        subscription_attributes = await sns_client.get_subscription_attributes(
            subscription_arn=service_subscriptions['SubscriptionArn']
        )

        assert subscription_attributes['Attributes'].get('FilterPolicy', {}) \
               == json.dumps(self.filters)

    async def confirm_permission(self, sns_client):
        session = BotoSession.get_session()

        async with session.create_client('sqs', endpoint_url=self.endpoint_url) as client:
            policy_attributes = await client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=['Policy']
            )

        policies = json.loads(policy_attributes['Attributes']['Policy'])
        statement = policies['Statement'][0]

        # need "Effect": "Allow", "Action": "SQS:SendMessage"
        assert statement['Effect'] == "Allow"
        assert statement['Action'] == "SQS:SendMessage"
        assert statement['Condition']['ArnEquals']['aws:SourceArn'] == sns_client.topic_arn

    @property
    def filters(self):
        if self._filters is None:
            processed_filters = []

            for filters in settings.INIESTA_SQS_CONSUMER_FILTERS:
                event = filters.split('.')
                assert len(event) == 2

                if event[1] == "*":
                    processed_filters.append({"prefix": f"{event[0]}."})
                else:
                    processed_filters.append(filters)
            if len(processed_filters) > 0:
                self._filters = {settings.INIESTA_SNS_EVENT_KEY: processed_filters}
            else:
                self._filters = {}
        return self._filters

    def start_receiving_messages(self, loop=None):
        self._receive_messages = True

        if loop is None:
            loop = asyncio.get_event_loop()

        self._polling_task = loop.create_task(self._poll())
        self._loop = loop

    async def stop_receiving_messages(self):
        self._receive_messages = False
        self._polling_task.cancel()
        await self.lock_manager.destroy()

    async def handle_message(self, message):
        """

        :param message:
        :type message: instance of SQSMessage
        :return:
        """
        lock = None

        try:
            lock = await self.lock_manager.lock(self.lock_key.format(message_id=message.message_id))
            if not lock.valid:
                raise LockError(f"Could not acquire lock for {message.message_id}")

            handler = self.handlers[message.event]
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

    def handle_error(self, exc):

        message = exc.message
        handler = getattr(exc, "handler", None)

        extra = {
            "iniesta_pass": message.event,  # TODO: get insanic event
            "sqs_message_id": message.message_id,
            "sqs_receipt_handle": message.receipt_handle,
            "sqs_md5_of_body": message.md5_of_body,
            "sqs_message_body": message.raw_body,
            "sqs_attributes": json.dumps(message.attributes),
            "handler_name": handler.__qualname__ if handler else None,
        }

        error_logger.critical(f"[INIESTA] Error while handling message: {str(exc)}", exc_info=exc, extra=extra)

    async def handle_success(self, client, message):

        # if success must delete message from sqs
        logger.info(f"[INIESTA] Message handled successfully: msg_id={message.message_id}")
        resp = await client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=message.receipt_handle
        )
        logger.debug(f"[INIESTA] Message deleted: msg_id={message.message_id} "
                         f"receipt_handle={message.receipt_handle}")
        return resp


    async def _poll(self):

        session = BotoSession.get_session()
        client = session.create_client('sqs', endpoint_url=self.endpoint_url)

        try:
            while self._loop.is_running() and self._receive_messages:
                try:
                    response = await client.receive_message(
                        QueueUrl = self.queue_url,
                        MaxNumberOfMessages = settings.INIESTA_SQS_RECEIVE_MESSAGE_MAX_NUMBER_OF_MESSAGES,
                        WaitTimeSeconds = settings.INIESTA_SQS_RECEIVE_MESSAGE_WAIT_TIME_SECONDS,
                        AttributeNames = ['All'],
                        MessageAttributeNames = ['All']
                    )
                except botocore.exceptions.ClientError as e:
                    error_logger.critical(f"[INIESTA] [{e.response['Error']['Code']}]: {e.response['Error']['Message']}")
                else:
                    event_tasks = [asyncio.ensure_future(self.handle_message(SQSMessage(message)))
                                   for message in response.get('Messages', [])]

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
        except Exception as e:
            if self._receive_messages and self._loop.is_running():
                error_logger.critical("[INIESTA] POLLING TASK RESTARTING")
                self._polling_task = self._loop.create_task(self._poll())
            error_logger.exception("[INIESTA] POLLING EXCEPTION CAUGHT")
        finally:
            await client.close()

        return "Shutdown"

    @classmethod
    def handler(cls, event):
        def register_handler(func):
            cls.add_handler(func, event)
            return func

        return register_handler

    @classmethod
    def add_handler(cls, handler, event):
        if event in cls.handlers.keys():
            raise ValueError(f"Handler for event [{event}] already exists.")

        args = [key for key in signature(handler).parameters.keys()]
        if args:
            cls.handlers.update({event: handler})
        else:
            raise ValueError(
                "Required parameter `request` missing "
                "in the {0}() route?".format(handler.__name__)
            )

    async def hook_post_receive_message_handler(self):
        pass

    # async def send_message(self):



    # async def send_message(self, message):
    #     try:
    #         await self.client.send_message(QueueUrl=self.queue_url, MessageBody=message)
    #     except botocore.exceptions.ClientError as err:
    #         if err.response['Error']['Code'] == \
    #                 'AWS.SimpleQueueService.NonExistentQueue':
    #             print("Queue {0} does not exist".format(QUEUE_NAME))
    #             await self.client.close()
    #         else:
    #             raise
