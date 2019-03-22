import asyncio
import boto3
import pytest
import ujson as json
import uuid

from insanic.conf import settings

from iniesta.exceptions import StopPolling
from iniesta import Iniesta
from iniesta.sns import SNSClient
from iniesta.sqs import SQSClient

from .infra import SNSInfra, SQSInfra


class TestSNSSQSIntegration(SQSInfra, SNSInfra):

    run_local = False

    @pytest.fixture(autouse=True)
    def cancel_polling(self, monkeypatch, create_service_sqs):

        sqs = boto3.resource('sqs')

        async def mock_hook_post_message_handler(queue_url):
            queue = sqs.Queue(queue_url)
            if int(queue.attributes['ApproximateNumberOfMessages']) == 0:
                raise StopPolling("Stop")

        from functools import partial
        with_counter = partial(mock_hook_post_message_handler, queue_url=create_service_sqs['QueueUrl'])

        monkeypatch.setattr(SQSClient, 'hook_post_receive_message_handler', with_counter)

    @pytest.fixture(scope='function')
    async def sns_client(self, create_global_sns, sns_endpoint_url):
        return await SNSClient.initialize(
            topic_arn=create_global_sns['TopicArn'],
            endpoint_url=sns_endpoint_url,
        )

    @pytest.fixture(scope='function')
    async def sqs_client(self, sqs_endpoint_url, sns_client):
        client = await SQSClient.initialize(
            queue_name=self.queue_name,
            endpoint_url=sqs_endpoint_url
        )
        yield client

        SQSClient.handlers = {}

    async def test_integration(self, start_local_aws, create_service_sqs, create_sqs_subscription,
                               add_permissions, sns_client, sqs_client, loop):

        some_id = uuid.uuid4().hex
        event = "Request.xavi"
        received_messages = []

        @SQSClient.handler(event)
        async def handler(message, *args, **kwargs):
            assert message.body['id'] == some_id
            received_messages.append(message)

            return True

        try:
            response = await sns_client.publish_event(event="Request", message=json.dumps({"id": some_id}),
                                                      round="one")
        except Exception as e:
            raise

        sqs_client.start_receiving_messages()

        await sqs_client._polling_task

        assert len(received_messages) == 1
        assert received_messages[0].body['id'] == some_id
        assert received_messages[0].event == event


        await sqs_client.lock_manager.destroy()


    async def test_filters(self, start_local_aws, create_sqs_subscription,
                           sqs_client, sns_client, add_permissions):
        received_messages = []

        @SQSClient.handler("RequestTestEvent1.iniesta")
        async def handler(message, *args, **kwargs):
            assert message.body['id'] == some_id
            received_messages.append(message)

            return True


        publish_tasks = []
        for i in range(10):
            publish_tasks.append(asyncio.ensure_future(
                sns_client.publish_event(
                    event="1RequestTestEvent1",
                    message=json.dumps({"id": i}),
                    round=i
                )))

        await asyncio.gather(*publish_tasks)

        sqs_client.start_receiving_messages()

        await sqs_client._polling_task

        assert len(received_messages) == 0

        await sqs_client.lock_manager.destroy()


    async def test_delete_sqs_message(self, start_local_aws, create_sqs_subscription,
                                      add_permissions, sqs_client, sns_client, monkeypatch):

        real_handle_success = SQSClient.handle_success

        delete_messages = []
        async def wrap_handle_success(self, client, message):
            delete_messages.append(message)
            resp = await real_handle_success(self, client, message)

            assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
        monkeypatch.setattr(SQSClient, 'handle_success', wrap_handle_success)


        received_messages = []

        @SQSClient.handler(f"Request.xavi")
        async def handler(message, *args, **kwargs):
            received_messages.append(message)
            return True

        publish_tasks = []
        for i in range(10):
            publish_tasks.append(asyncio.ensure_future(
                sns_client.publish_event(
                    event="Request",
                    message=json.dumps({"id": i}),
                    round=i
                )))

        await asyncio.gather(*publish_tasks)
        sqs_client.start_receiving_messages()
        await sqs_client._polling_task
        assert len(received_messages) == 10
        assert len(delete_messages) == 10
        assert sorted(received_messages, key=lambda x: x.message_id) == sorted(delete_messages, key=lambda x: x.message_id)


        await sqs_client.lock_manager.destroy()

    async def test_confirm_permissions(self, start_local_aws, create_sqs_subscription,
                                       add_permissions, sqs_client, sns_client):
        await sqs_client.confirm_permission(sns_client)

