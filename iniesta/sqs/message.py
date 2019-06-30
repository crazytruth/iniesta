import botocore
import hashlib
import ujson as json

from insanic.conf import settings
from iniesta.loggers import error_logger
from iniesta.messages import MessageAttributes
from iniesta.sessions import BotoSession

empty = object()

VALID_SEND_MESSAGE_ARGS = [
    'MessageBody',
    'DelaySeconds',
    'MessageAttributes',
    'MessageDeduplicationId',
    'MessageGroupId'
]

ERROR_MESSAGES = {
    "delay_seconds_out_of_bounds": 'Delay Seconds must be between 0 and 900 inclusive. Got {value}.',
    "delay_seconds_type_error": 'Delay Seconds must be an integer. Got {value}.'
}


class SQSMessage(MessageAttributes):

    def __init__(self, client, message):
        super().__init__()
        self.client = client
        self['MessageBody'] = message
        self.message_id = None
        self.original_message = None
        self.receipt_handle = None
        self.md5_of_body = None
        self.attributes = None

    @classmethod
    def from_sqs(cls, client, message):
        """
        A helper method that unpacks everything from receive_message

        :param client: SQSClient instance from which the message came from
        :param message: The dict from receive_message
        :type message: dict
        :return:
        """

        try:
            message_object = cls(client, message['Body'])
            message_object.original_message = message
            message_object.message_id = message['MessageId']
            message_object.receipt_handle = message['ReceiptHandle']
            message_object.md5_of_body = message['MD5OfBody']
            message_object.attributes = message['Attributes']

            message_object['MessageAttributes'] = message.get('MessageAttributes', {})
        except KeyError as e:
            raise ValueError(f"SQS Message is invalid: {e.args[0]}")
        else:
            return message_object

    def __eq__(self, other):
        if self.message_id is not None:
            return self.message_id == other.message_id
        else:
            return False

    @property
    def delay_seconds(self):
        return self.get('DelaySeconds', 0)

    @delay_seconds.setter
    def delay_seconds(self, value):
        if not isinstance(value, int):
            raise TypeError(ERROR_MESSAGES['delay_seconds_type_error'].format(value=value))
        elif value < 0 or value > 900:
            raise ValueError(ERROR_MESSAGES['delay_seconds_out_of_bounds'].format(value=value))

        self['DelaySeconds'] = value

    @property
    def raw_body(self):
        return self['MessageBody']

    @property
    def body(self):
        try:
            return json.loads(self.raw_body)
        except ValueError:
            return self.raw_body

    @property
    def event(self):
        return self.message_attributes.get(settings.INIESTA_SNS_EVENT_KEY, None)

    def checksum_body(self):
        return hashlib.md5(self['MessageBody'].encode('utf-8')).hexdigest() == self.md5_of_body

    @property
    def message_attributes(self):

        _message_attributes = {}

        for attribute, attribute_value in self['MessageAttributes'].items():
            data_type = attribute_value['DataType'].split('.', 1)[0]

            if data_type == "Number":
                data_type = "String"

            _message_attributes.update({attribute: attribute_value[f'{data_type}Value']})

        return _message_attributes

    async def send(self):
        """
        Sends the message to the queue defined in client

        :return:
        """
        session = BotoSession.get_session()
        try:
            async with session.create_client('sqs', region_name=self.client.region_name,
                                             endpoint_url=self.client.endpoint_url,
                                             aws_access_key_id=BotoSession.aws_access_key_id,
                                             aws_secret_access_key=BotoSession.aws_secret_access_key
                                             ) as client:
                message = await client.send_message(QueueUrl=self.client.queue_url,
                                                    **{k:v for k,v in self.items()
                                                       if k in VALID_SEND_MESSAGE_ARGS})
                self.message_id = message['MessageId']
                self.md5_of_body = message['MD5OfMessageBody']
                return self
        except botocore.exceptions.ClientError as e:
            error_logger.critical(f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']}")
            raise
        except Exception:
            error_logger.exception('Sending SQS message failed.')
            raise

