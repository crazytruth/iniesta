from typing import Union, Any

import botocore
import ujson as json

from insanic.conf import settings

from iniesta.log import logger, error_logger
from iniesta.sessions import BotoSession
from iniesta.messages import MessageAttributes

#: A constant for the max body size SNS can publish.
MAX_BODY_SIZE: int = 1024 * 256


class SNSMessage(MessageAttributes):
    """
    A SNS Message object that will be serialized to send.
    """

    def __init__(self, message: str = ""):

        super().__init__()
        self["Message"] = message
        self["MessageStructure"] = "string"
        self["MessageAttributes"] = {}

    @property
    def event(self) -> Union[str, None]:
        """
        The event this message is attached to. Returns :code:`None` if
        event is not set.
        """
        try:
            return self.message_attributes[settings.INIESTA_SNS_EVENT_KEY][
                "StringValue"
            ]
        except KeyError:
            return None

    @property
    def message(self) -> Any:
        """
        The message body.
        """
        return self["Message"]

    @message.setter
    def message(self, value: str) -> None:
        """
        Setter for the message body of the request.

        :param value: Any json serializable value.
        :raises TypeError: If the value is not able to be json dumpable.
        :raises ValueError: If the message is too long to be published.
        """
        if not isinstance(value, str):
            try:
                value = json.dumps(value)
            except Exception:
                raise TypeError("Message must be a string.")

        if len(value.encode("utf8")) > MAX_BODY_SIZE:
            raise ValueError(
                f"Message is too long! Max is {MAX_BODY_SIZE} bytes. "
                f"{len(value.encode('utf8'))} bytes calculated."
            )

        self["Message"] = value

    @property
    def size(self) -> int:
        """
        The size of this message.
        """
        return len(json.dumps(self.data).encode("utf8"))

    @property
    def subject(self) -> str:
        """
        Subject to be used when sending to email subscription.
        """
        return self["Subject"]

    @subject.setter
    def subject(self, value: str) -> None:
        """
        :raises TypeError: If the value is not a string.
        """
        if not isinstance(value, str):
            raise TypeError("Subject must be a string.")
        self["Subject"] = value

    @property
    def message_structure(self) -> str:
        """
        The message structure.
        """
        return self["MessageStructure"]

    @message_structure.setter
    def message_structure(self, value: str) -> None:
        """
        Setter for message structure.
        :param value: Must be the literal value :code:`"json"` or :code:`"string"`.
        :raises ValueError: If the value is not either "json" or "string"
        """
        if value not in ["json", "string"]:
            raise ValueError(
                "MessageStructure must either be 'json' or 'string'."
            )

        self["MessageStructure"] = value

    async def publish(self) -> dict:
        """
        Serializes this message and publishes this message to SNS.

        :return: The response of the publish request to SNS.
        """

        session = BotoSession.get_session()
        try:
            async with session.create_client(
                "sns",
                region_name=BotoSession.aws_default_region,
                endpoint_url=self.client.endpoint_url,
                aws_access_key_id=BotoSession.aws_access_key_id,
                aws_secret_access_key=BotoSession.aws_secret_access_key,
            ) as client:
                message = await client.publish(
                    TopicArn=self.client.topic_arn, **self
                )
                logger.debug(
                    f"[INIESTA] Published ({self.event}) with "
                    f"the following attributes: {self}"
                )
                return message
        except botocore.exceptions.ClientError as e:
            error_logger.critical(
                f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']}"
            )
            raise
        except Exception:
            error_logger.exception("Publishing SNS Message Failed!")
            raise

    @classmethod
    def create_message(
        cls,
        client,
        *,
        event: str,
        message: Any,
        version: int = 1,
        raw_event: bool = False,
        **message_attributes,
    ):
        """
        A factory method to initialize an event message.

        :param client: The initialized SNSClient
        :type client: :code:`SNSClient`
        :param event: The event this message will publish.
        :param message: The message body to publish.
        :param version: Version of the message.
        :param raw_event: If the event should be passed in as itself.
        :param message_attributes: Any message attributes
        :return: Instantiated instance of self.
        :rtype: :code:`SNSMessage`
        """

        message_object = cls(message)
        message_object.message = message

        for ma, mv in message_attributes.items():
            message_object.add_attribute(ma, mv)

        message_object.add_event(event, raw=raw_event)
        message_object.add_number_attribute("version", version)
        message_object.client = client

        return message_object
