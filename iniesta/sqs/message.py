from typing import Any

import hashlib
import ujson as json
from botocore.exceptions import ClientError

from insanic.conf import settings
from iniesta.log import error_logger
from iniesta.messages import MessageAttributes
from iniesta.sessions import BotoSession

empty = object()

VALID_SEND_MESSAGE_ARGS = [
    "MessageBody",
    "DelaySeconds",
    "MessageAttributes",
    "MessageDeduplicationId",
    "MessageGroupId",
]

ERROR_MESSAGES = {
    "delay_seconds_out_of_bounds": "Delay Seconds must be between 0 and 900 inclusive. Got {value}.",
    "delay_seconds_type_error": "Delay Seconds must be an integer. Got {value}.",
}


class SQSMessage(MessageAttributes):
    """
    The Message object that will be used to send a message to SQS.

    :param client: The client that will be sending this message.
    :type client: :code:`SQSClient`
    :param message: The message to send. A json serializable value.
    """

    def __init__(self, client, message: Any) -> None:

        super().__init__()
        self.client = client
        self["MessageBody"] = message
        self.message_id = None
        self.original_message = None
        self.receipt_handle = None
        self.md5_of_body = None
        self.attributes = None

    @classmethod
    def from_sqs(cls, client, message: Any):
        """
        A helper method that unpacks everything from receive_message

        :param client: SQSClient instance from which the message came from
        :type client: :code:`SQSClient`
        :param message: The message from receive_message when polling SQS.
        :return: A initialized SQSMessage instance.
        :rtype: :code:`SQSMessage`
        """

        try:
            message_object = cls(client, message["Body"])
            message_object.original_message = message
            message_object.message_id = message["MessageId"]
            message_object.receipt_handle = message["ReceiptHandle"]
            message_object.md5_of_body = message["MD5OfBody"]
            message_object.attributes = message["Attributes"]

            message_object["MessageAttributes"] = message.get(
                "MessageAttributes", {}
            )
        except KeyError as e:  # pragma: no cover
            raise ValueError(f"SQS Message is invalid: {e.args[0]}")
        else:
            return message_object

    def __eq__(self, other):
        if self.message_id is not None:
            return self.message_id == other.message_id
        else:
            return False

    @property
    def delay_seconds(self) -> int:
        """
        The length of time in seconds to delay the message.
        """
        return self.get("DelaySeconds", 0)

    @delay_seconds.setter
    def delay_seconds(self, value: int) -> None:
        """
        To set the length of time in seconds to delay the message.

        :raises TypeError: If the value is not an int.
        :raises ValueError: If the value is not between 0 and 900.
        """
        if not isinstance(value, int):
            raise TypeError(
                ERROR_MESSAGES["delay_seconds_type_error"].format(value=value)
            )
        elif value < 0 or value > 900:
            raise ValueError(
                ERROR_MESSAGES["delay_seconds_out_of_bounds"].format(
                    value=value
                )
            )

        self["DelaySeconds"] = value

    @property
    def raw_body(self):
        """
        The raw body of the message.
        """
        return self["MessageBody"]

    @property
    def body(self):
        """
        The body as a python object.
        """
        try:
            return json.loads(self.raw_body)
        except ValueError:
            return self.raw_body

    @property
    def event(self) -> str:
        """
        The event that this message was received as.
        """
        return self.message_attributes.get(settings.INIESTA_SNS_EVENT_KEY, None)

    def checksum_body(self) -> bool:
        """
        Verifies the body was properly received.
        """
        return (
            hashlib.md5(self["MessageBody"].encode("utf-8")).hexdigest()
            == self.md5_of_body
        )

    @property
    def message_attributes(self) -> dict:
        """
        Any message attributes attached to this body.
        Refer to https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-message-metadata.html#sqs-message-attributes
        """

        _message_attributes = {}

        for attribute, attribute_value in self["MessageAttributes"].items():
            data_type = attribute_value["DataType"].split(".", 1)[0]

            if data_type == "Number":
                data_type = "String"

            _message_attributes.update(
                {attribute: attribute_value[f"{data_type}Value"]}
            )

        return _message_attributes

    async def send(self):
        """
        Sends this message to the queue defined in client.

        :rtype: :code:`SQSMessage`
        :raises botocore.exceptions.ClientError: If there was an issue when sending the message to SQS.
        """
        session = BotoSession.get_session()
        try:
            async with session.create_client(
                "sqs",
                region_name=BotoSession.aws_default_region,
                endpoint_url=self.client.endpoint_url,
                aws_access_key_id=BotoSession.aws_access_key_id,
                aws_secret_access_key=BotoSession.aws_secret_access_key,
            ) as client:
                message = await client.send_message(
                    QueueUrl=self.client.queue_url,
                    **{
                        k: v
                        for k, v in self.items()
                        if k in VALID_SEND_MESSAGE_ARGS
                    },
                )
                self.message_id = message["MessageId"]
                self.md5_of_body = message["MD5OfMessageBody"]
                return self
        except ClientError as e:
            error_logger.critical(
                f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']}"
            )
            raise
        except Exception:  # pragma: no cover
            error_logger.exception("Sending SQS message failed.")
            raise
