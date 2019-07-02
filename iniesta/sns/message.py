import botocore
import ujson as json

from insanic.conf import settings

from iniesta.loggers import logger, error_logger
from iniesta.sessions import BotoSession
from iniesta.messages import MessageAttributes


class SNSMessage(MessageAttributes):

    MAX_BODY_SIZE = 1024 * 256

    def __init__(self, message=""):
        super().__init__()
        self['Message'] = message
        self['MessageStructure'] = 'string'
        self['MessageAttributes'] = {}

    @property
    def event(self):
        try:
            return self.message_attributes[settings.INIESTA_SNS_EVENT_KEY]['StringValue']
        except KeyError:
            return None

    @property
    def message(self):
        return self['Message']

    @message.setter
    def message(self, value):
        if not isinstance(value, str):
            try:
                value = json.dumps(value)
            except:
                raise ValueError("Message must be a string.")

        if len(value.encode('utf8')) > self.MAX_BODY_SIZE:
            raise ValueError(f"Message is too long! Max is {self.MAX_BODY_SIZE} bytes. "
                             f"{len(value.encode('utf8'))} bytes calculated.")

        self['Message'] = value

    @property
    def size(self):
        return len(json.dumps(self).encode('utf8'))

    @property
    def subject(self):
        return self['Subject']

    @subject.setter
    def subject(self, value):
        if not isinstance(value, str):
            raise ValueError("Subject must be a string.")
        self['Subject'] = value

    @property
    def message_structure(self):
        return self['MessageStructure']

    @message_structure.setter
    def message_structure(self, value):
        if value not in ['json', 'string']:
            raise ValueError("MessageStructure must either be 'json' or 'string'.")

        self['MessageStructure'] = value

    async def publish(self):
        """
        Publishes this message to SNS.

        :return: returns the response of the publish request
        """

        session = BotoSession.get_session()
        try:
            async with session.create_client('sns', region_name=BotoSession.aws_default_region,
                                             endpoint_url=self.client.endpoint_url,
                                             aws_access_key_id=BotoSession.aws_access_key_id,
                                             aws_secret_access_key=BotoSession.aws_secret_access_key
                                             ) as client:
                message = await client.publish(TopicArn=self.client.topic_arn, **self)
                logger.debug(f"[INIESTA] Published ({self.event}) with "
                             f"the following attributes: {self}")
                return message
        except botocore.exceptions.ClientError as e:
            error_logger.critical(f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']}")
            raise
        except Exception:
            error_logger.exception("Publishing SNS Message Failed!")
            raise

    @classmethod
    def create_message(cls, client, *, event, message, version=1, **message_attributes):
        """
        Helper method to initialize an event message.

        :param client: The initialized SNSClient
        :type client: SNSClient
        :param event: The event this message will publish
        :type event: string
        :param message: The message body to include
        :type message: str or json dumpable object
        :param version: Version
        :type version: int
        :param message_attributes: Any message attributes
        :type message_attributes: dict
        :return: instantiated message
        :rtype: SNSMessage
        """

        message_object = cls(message)
        message_object.message = message

        for ma, mv in message_attributes.items():
            message_object.add_attribute(ma, mv)

        message_object.add_event(event)
        message_object.add_number_attribute('version', version)
        message_object.client = client

        return message_object
