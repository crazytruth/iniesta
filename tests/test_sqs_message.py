import uuid

import pytest
from botocore.exceptions import ClientError

from iniesta import Iniesta
from iniesta.sqs import SQSClient, SQSMessage
from iniesta.sqs.message import ERROR_MESSAGES

from .infra import SQSInfra


class TestSQSMessage(SQSInfra):
    queue_name = "iniesta-tests-xavi"

    @pytest.fixture
    def sqs_client(self, insanic_application, create_service_sqs):
        Iniesta.load_config(insanic_application.config)
        SQSClient.queue_urls = {
            SQSClient.default_queue_name(): create_service_sqs["QueueUrl"]
        }
        sqs_client = SQSClient()

        return sqs_client

    def test_initialize(self, sqs_client):
        message = SQSMessage(sqs_client, "message")

        assert message.client == sqs_client
        assert message["MessageBody"] == "message"
        assert message.message_id is None
        assert message.original_message is None
        assert message.receipt_handle is None
        assert message.md5_of_body is None

    def test_message_equality(self, sqs_client):

        message1 = SQSMessage(sqs_client, "message1")
        message2 = SQSMessage(sqs_client, "message2")

        assert message1.message_id is None
        assert message2.message_id is None
        assert message1 != message2

        message1.message_id = 1
        message2.message_id = 2

        assert message1 != message2

        message2.message_id = 1

        assert message1 == message2

    def test_delay_seconds(self, sqs_client):
        message = SQSMessage(sqs_client, "message")

        assert message.delay_seconds == 0

        message.delay_seconds = 1

        assert message.delay_seconds == 1

        message.delay_seconds = 900
        assert message.delay_seconds == 900

        message.delay_seconds = 0
        assert message.delay_seconds == 0

        with pytest.raises(
            TypeError,
            match=ERROR_MESSAGES["delay_seconds_type_error"].format(value="a"),
        ):
            message.delay_seconds = "a"

        with pytest.raises(
            ValueError,
            match=ERROR_MESSAGES["delay_seconds_out_of_bounds"].format(
                value=901
            ),
        ):
            message.delay_seconds = 901

        with pytest.raises(
            ValueError,
            match=ERROR_MESSAGES["delay_seconds_out_of_bounds"].format(
                value=-1
            ),
        ):
            message.delay_seconds = -1

    async def test_send(
        self, create_service_sqs, sqs_client, aws_client_kwargs
    ):

        random_uuid = uuid.uuid4().hex

        message = SQSMessage(sqs_client, random_uuid)
        message.add_number_attribute("number", 1)
        message.add_binary_attribute("binary", b"b")
        message.add_string_attribute("string", "s")
        message.add_list_attribute("list", ["c", "d"])
        message = await message.send()

        assert message.message_id is not None
        assert message.md5_of_body is not None

        # try get message from queue

        sqs_boto_client = self.aws_client("sqs", **aws_client_kwargs)
        sqs_message = sqs_boto_client.receive_message(
            QueueUrl=sqs_client.queue_url,
            AttributeNames=["All"],
            MessageAttributeNames=["All"],
        )

        assert sqs_message is not None
        received_message = SQSMessage.from_sqs(
            sqs_client, sqs_message["Messages"][0]
        )
        assert received_message == message
        assert received_message.body == message.body == random_uuid

        assert received_message.message_attributes == message.message_attributes
        assert received_message.checksum_body()

    async def test_send_failure_client_error(
        self, create_service_sqs, sqs_client, aws_client_kwargs
    ):
        random_uuid = uuid.uuid4().hex
        sqs_client.queue_url = sqs_client.queue_url + "1"

        message = SQSMessage(sqs_client, random_uuid)

        with pytest.raises(ClientError):
            await message.send()
