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

        try:
            message_object = cls(client, message['Body'])
            message_object.original_message = message
            message_object.message_id = message['MessageId']
            message_object.receipt_handle = message['ReceiptHandle']
            message_object.md5_of_body = message['MD5OfBody']
            message_object.attributes = message['Attributes']

            message_object['MessageAttributes'] = message.get('MessageAttributes', {})

            try:
                message_object.body = json.loads(message_object['MessageBody'])
            except ValueError:
                message_object.body = message_object['MessageBody']
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
            raise ValueError(f'Delay Seconds must be an integer. Got {value}.')
        elif value < 0 or value > 900:
            raise ValueError(f'Delay Seconds must be between 0 and 900 inclusive. Got {value}.')

        self['DelaySeconds'] = value

    @property
    def raw_body(self):
        return self['MessageBody']

    @property
    def event(self):
        return self.message_attributes[settings.INIESTA_SNS_EVENT_KEY]['StringValue']

    def checksum_body(self):
        return hashlib.md5(self['MessageBody'].encode('utf-8')).hexdigest() == self.md5_of_body

    @staticmethod
    def _unpack_message_attributes(message_attributes):

        _message_attributes = {}

        for attribute, attribute_value in message_attributes.items():
            data_type = attribute_value['DataType'].split('.', 1)[0]

            if data_type == "Number":
                data_type = "String"

            _message_attributes.update({attribute: attribute_value[f'{data_type}Value']})

        return _message_attributes

    # @classmethod
    # def create_message(cls, ):

    async def send(self):
        session = BotoSession.get_session()
        try:
            async with session.create_client('sqs',
                                             endpoint_url=self.client.endpoint_url) as client:
                message = await client.send_message(QueueUrl=self.client.queue_url,
                                                    **{k:v for k,v in self.items()
                                                       if k in VALID_SEND_MESSAGE_ARGS})
                return message
        except botocore.exceptions.ClientError as e:
            error_logger.critical(f"[{e.response['Error']['Code']}]: {e.response['Error']['Message']}")
            raise
        except Exception:
            error_logger.exception('Sending SQS message failed.')
            raise

