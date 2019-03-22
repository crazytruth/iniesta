import asyncio
import boto3
import botocore
import pytest
import ujson as json

from insanic.conf import settings
from iniesta.sqs import SQSClient

from .infra import SQSInfra


class TestSQSClient(SQSInfra):

    @pytest.fixture(autouse=True)
    def reset_sqs_client(self):
        yield
        SQSClient.handlers = {}
        SQSClient.queue_urls = {}


    @pytest.fixture
    def queue_messages(self, create_service_sqs, sqs_endpoint_url):

        sqs = boto3.client('sqs', endpoint_url=sqs_endpoint_url)
        messages = []
        for i in range(10):
            resp = sqs.send_message(
                QueueUrl=create_service_sqs['QueueUrl'],
                MessageBody=json.dumps({"message_number": i}),
                MessageAttributes={
                    settings.INIESTA_SNS_EVENT_KEY: {
                        "DataType": "String",
                        "StringValue": "test_event"
                    }
                }
            )
            messages.append(resp)
        return messages

    async def test_sqs_client_initialize_queue_does_not_exist(self, start_local_aws, sqs_endpoint_url):
        with pytest.raises(botocore.exceptions.ClientError, match="") as exc_info:
            client = await SQSClient.initialize(queue_name='asdasdasda',
                                                endpoint_url=sqs_endpoint_url)

    async def test_sqs_client(self, start_local_aws, create_service_sqs, sqs_endpoint_url):
        client = await SQSClient.initialize(queue_name=self.queue_name,
                                            endpoint_url=sqs_endpoint_url)

        assert self.queue_name in client.queue_urls[self.queue_name]
        assert client.queue_url == create_service_sqs['QueueUrl']

    async def test_sqs_handler(self):

        @SQSClient.handler("something")
        def handler(*args, **kwargs):
            print(args)
            print(**kwargs)


        assert "something" in SQSClient.handlers

    async def test_receive_message(self, start_local_aws, create_service_sqs, sqs_endpoint_url,
                                   queue_messages, monkeypatch):
        message_number = []

        async def mock_handle_message(self, message):

            message_number.append(message.body['message_number'])

            return message, message_number

        async def mock_hook_post_message_handler(self):

            await self.stop_receiving_messages()

        monkeypatch.setattr(SQSClient, 'hook_post_receive_message_handler', mock_hook_post_message_handler)
        monkeypatch.setattr(SQSClient, 'handle_message', mock_handle_message)

        client = await SQSClient.initialize(queue_name=self.queue_name, endpoint_url=sqs_endpoint_url)
        client.start_receiving_messages()

        await client._polling_task

        assert len(message_number) == 10
        assert sorted(message_number) == list(range(10))

        await client.lock_manager.destroy()

    async def test_receive_message_with_error(self, start_local_aws, create_service_sqs, sqs_endpoint_url,
                                              queue_messages, monkeypatch):

        message_number = []

        async def mock_handle_message(self, message):
            def some_handler():
                pass

            message_number.append(message.body['message_number'])

            exc = RuntimeError("Some error happened!!")
            exc.message = message
            exc.handler = some_handler
            raise exc

        async def mock_hook_post_message_handler(self):
            if len(message_number) == 10:
                asyncio.Task.current_task().cancel()

        monkeypatch.setattr(SQSClient, 'hook_post_receive_message_handler', mock_hook_post_message_handler)
        monkeypatch.setattr(SQSClient, 'handle_message', mock_handle_message)

        client = await SQSClient.initialize(queue_name=self.queue_name,
                                            endpoint_url=sqs_endpoint_url)
        client.start_receiving_messages()

        await client._polling_task

        assert len(message_number) == 10
        assert sorted(message_number) == list(range(10))

        await client.lock_manager.destroy()

    def test_handler_register(self):
        event = "SomethingHappened.test"

        @SQSClient.handler(event)
        def handler_for_test_event(*args, **kwargs):

            return "test event"

        assert event in SQSClient.handlers
        assert SQSClient.handlers[event] == handler_for_test_event

    async def test_async_handler_register(self):
        event = "SomethingAsyncHappened.test"

        @SQSClient.handler(event)
        async def handler_for_test_event(*args, **kwargs):

            return "test event"

        assert event in SQSClient.handlers
        assert SQSClient.handlers[event] == handler_for_test_event

    def test_handler_duplicates(self):
        event = "DoubleHandlerRegistration"

        @SQSClient.handler(event)
        def handler_one(*args, **kwargs):
            return "one"

        assert event in SQSClient.handlers

        with pytest.raises(ValueError):
            @SQSClient.handler(event)
            def handler_two(*args, **kwargs):
                return "two"

    def test_class_handler(self):
        event = "ClassHandler"

        class SomeHandler:

            @SQSClient.handler(event)
            def handler(self, *args, **kwargs):
                return "class"

        assert event in SQSClient.handlers
        assert SQSClient.handlers[event] == SomeHandler.handler

    def test_class_async_handler(self):
        event = "ClassHandler"

        class SomeHandler:

            @SQSClient.handler(event)
            async def handler(self, *args, **kwargs):
                return "class"

        assert event in SQSClient.handlers
        assert SQSClient.handlers[event] == SomeHandler.handler

    async def test_handle_message(self, start_local_aws, create_service_sqs, sqs_endpoint_url,
                                  queue_messages, monkeypatch):
        """
        SAMPLE MESSAGE FROM AWS SQS
        {
            'MessageId': '0f9be9cc-04ee-4e55-920f-f928086d2ca7',
            'ReceiptHandle': 'AQEBu2GxhOzv8C07Tzs0Xj2KEQaaG4zBvTgLbexrtcnSHXyKSa7xH5JgnnvljKP3GL4u/+mmDGz2h4fkuyDDQSKxo5PVpP8aAk7h3SXIGkv4MTFRyTaKx4mYmeND4lRwb3wBlRDod9nUpamByMu6jKxQHbyqVG+HmSv21GTqRJk36N21k+x5buHR0DkG01NiH4zLGU0jb7FwbNGbtmRO1Pqapsap1J7ATQdl+wvxEnwRsyIXMCdNCui6RA8hvPzomKb3jss6D3f1k9XyJFoqw22ieSj7LnJ71GScz6fkNoovbBFXQf+ub4NG2TgRxOOzT+/1mJr7ddI/Ov2PEZbzET5b85trS2WtRKWfUoHtXlb2P5w8LCdR+++U/GnUIwRMlyxFRLUCBC4XXIfoiLYsZxS4Kw==',
            'MD5OfBody': 'd1691fe9a8e4e93beed42d7a1521878a',
            'Body': '{"message_number":4}',
            'Attributes': {
                'SenderId': 'AIDAJDPU3AEPJEAEBCW2W',
                'ApproximateFirstReceiveTimestamp': '1552309481056',
                'ApproximateReceiveCount': '2',
                'SentTimestamp': '1552309480314'
            },
            'MD5OfMessageAttributes': 'c45f9191837250ab2cc208d5f0362290',
            'MessageAttributes': {
                'iniesta_pass': {
                    'StringValue': 'test_event',
                    'DataType': 'String'
                }
            }
        }
        :param start_local_aws:
        :param create_service_sqs:
        :param sqs_endpoint_url:
        :param queue_messages:
        :param monkeypatch:
        :return:
        """


        message_tracker = []

        @SQSClient.handler("test_event")
        def event_handler(message, **kwargs):

            message_tracker.append(message.body['message_number'])

            return "something"


        client = await SQSClient.initialize(queue_name=self.queue_name, endpoint_url=sqs_endpoint_url)
        # poll_task = asyncio.ensure_future(client._poll())
        client.start_receiving_messages()

        async def mock_hook_post_message_handler(self):
            if len(message_tracker) == 10:
                await self.stop_receiving_messages()

        monkeypatch.setattr(SQSClient, 'hook_post_receive_message_handler', mock_hook_post_message_handler)

        await client._polling_task

        assert len(message_tracker) == 10

    async def test_handle_message_lock(self, start_local_aws, create_service_sqs, sqs_endpoint_url,
                                       queue_messages, monkeypatch, redisdb, caplog):
        message_tracker = []

        @SQSClient.handler('test_event')
        def event_handler(message, **kwargs):
            message_tracker.append(message.body['message_number'])

            return "mess"

        client = await SQSClient.initialize(queue_name=self.queue_name,
                                            endpoint_url=sqs_endpoint_url)

        client.start_receiving_messages()

        async def mock_hook_post_message_hander(self):

            await self.stop_receiving_messages()

        monkeypatch.setattr(SQSClient, 'hook_post_receive_message_handler', mock_hook_post_message_hander)

        import uuid
        message_ids = []
        # set lock
        for m in queue_messages:
            redisdb.set(SQSClient.lock_key.format(message_id=m['MessageId']), str(uuid.uuid4()))
            message_ids.append(m['MessageId'])

        await client._polling_task

        logged_messaged_ids = [log.sqs_message_id for log in caplog.records if hasattr(log, 'sqs_message_id')]
        for mid in message_ids:
            assert mid in logged_messaged_ids

        for log in caplog.records:
            if hasattr(log, "sqs_message_id"):
                assert "Can not acquire the lock" in log.msg

        await client.lock_manager.destroy()
