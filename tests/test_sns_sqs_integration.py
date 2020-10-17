import asyncio
import pytest
import ujson as json
import uuid

from iniesta.exceptions import StopPolling
from iniesta.sns import SNSClient
from iniesta.sqs import SQSClient
from iniesta.sessions import BotoSession

from .infra import SNSInfra, SQSInfra


class TestSNSSQSIntegration(SQSInfra, SNSInfra):
    @pytest.fixture(autouse=True)
    def cancel_polling(self, monkeypatch, create_service_sqs):
        async def mock_hook_post_message_handler(queue_url):
            # NOTE: due to The security token included in the request is invalid, I comment out this please check it
            # sqs = botocore.resource('sqs', region_name=sqs_region_name,
            #                      aws_access_key_id=BotoSession.aws_access_key_id,
            #                      aws_secret_access_key=BotoSession.aws_secret_access_key)
            # queue = sqs.Queue(queue_url)
            # if int(queue.attributes['ApproximateNumberOfMessages']) == 0:
            #     raise StopPolling("Stop")
            sqs = self.aws_client(
                "sqs",
                endpoint_url=queue_url,
                aws_access_key_id=BotoSession.aws_access_key_id,
                aws_secret_access_key=BotoSession.aws_secret_access_key,
                region_name=BotoSession.aws_default_region,
            )
            response = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["ApproximateNumberOfMessages"],
            )

            if int(response["Attributes"]["ApproximateNumberOfMessages"]) == 0:
                raise StopPolling("Stop")

        from functools import partial

        with_counter = partial(
            mock_hook_post_message_handler,
            queue_url=create_service_sqs["QueueUrl"],
        )

        monkeypatch.setattr(
            SQSClient, "hook_post_receive_message_handler", with_counter
        )

    @pytest.fixture(scope="function")
    async def sns_client(self, create_global_sns):
        return await SNSClient.initialize(
            topic_arn=create_global_sns["TopicArn"]
        )

    @pytest.fixture(scope="function")
    async def sqs_client(self, sns_client):
        client = await SQSClient.initialize(queue_name=self.queue_name)
        yield client
        SQSClient.handlers = {}

    async def test_integration(
        self,
        create_service_sqs,
        create_sqs_subscription,
        add_permissions,
        sns_client,
        sqs_client,
        loop,
    ):

        some_id = uuid.uuid4().hex
        event = "Request.xavi"
        received_messages = []

        @SQSClient.handler(event)
        async def handler(_message, *args, **kwargs):
            assert _message.body["id"] == some_id
            received_messages.append(_message)
            return True

        try:
            message = sns_client.create_message(
                event="Request",
                message=json.dumps({"id": some_id}),
                round="one",
            )
            await message.publish()
        except Exception:
            raise

        sqs_client.start_receiving_messages()

        await sqs_client._polling_task

        assert len(received_messages) == 1
        assert received_messages[0].body["id"] == some_id
        assert received_messages[0].event == event

        await sqs_client.lock_manager.destroy()

    async def test_filters(
        self, create_sqs_subscription, sqs_client, sns_client, add_permissions,
    ):
        some_id = uuid.uuid4().hex
        received_messages = []

        @SQSClient.handler("RequestTestEvent1.iniesta")
        async def handler(_message, *args, **kwargs):
            assert _message.body["id"] == some_id
            received_messages.append(message)
            return True

        publish_tasks = []
        for i in range(10):
            message = sns_client.create_message(
                event="1RequestTestEvent1",
                message=json.dumps({"id": i}),
                round=i,
            )

            publish_tasks.append(asyncio.ensure_future(message.publish()))

        await asyncio.gather(*publish_tasks)

        sqs_client.start_receiving_messages()

        await sqs_client._polling_task

        assert len(received_messages) == 0

        await sqs_client.lock_manager.destroy()

    async def test_delete_sqs_message(
        self,
        create_sqs_subscription,
        add_permissions,
        sqs_client,
        sns_client,
        monkeypatch,
    ):
        real_handle_success = SQSClient.handle_success
        delete_messages = []

        async def wrap_handle_success(self, client, _message):
            delete_messages.append(_message)
            resp = await real_handle_success(self, client, _message)
            assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

        monkeypatch.setattr(SQSClient, "handle_success", wrap_handle_success)

        received_messages = []

        @SQSClient.handler("Request.xavi")
        async def handler(_message, *args, **kwargs):
            received_messages.append(_message)
            return True

        publish_tasks = []
        for i in range(10):
            message = sns_client.create_message(
                event="Request", message=json.dumps({"id": i}), round=i
            )
            publish_tasks.append(asyncio.ensure_future(message.publish()))

        await asyncio.gather(*publish_tasks)
        sqs_client.start_receiving_messages()
        await sqs_client._polling_task
        assert len(received_messages) > 0
        assert len(delete_messages) > 0
        assert sorted(received_messages, key=lambda x: x.message_id) == sorted(
            delete_messages, key=lambda x: x.message_id
        )

        await sqs_client.lock_manager.destroy()

    async def test_confirm_permissions(
        self, create_sqs_subscription, add_permissions, sqs_client, sns_client,
    ):
        await sqs_client.confirm_permission()

    async def test_confirm_subscription(
        self, create_sqs_subscription, add_permissions, sqs_client, sns_client,
    ):
        await asyncio.sleep(1)
        await sqs_client.confirm_subscription(sns_client.topic_arn)
