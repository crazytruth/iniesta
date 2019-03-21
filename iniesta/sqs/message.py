import hashlib
import ujson as json

from insanic.conf import settings


class SQSMessage:

    def __init__(self, message):
        try:
            self.original_message = message
            self.message_id = message['MessageId']
            self.receipt_handle = message['ReceiptHandle']
            self.md5_of_body = message['MD5OfBody']
            self.attributes = message['Attributes']

            self.raw_body = message['Body']
            self.raw_message_attributes = message.get('MessageAttributes', {})

            self.body = json.loads(self.raw_body)
            self.message_attributes = self._unpack_message_attributes(self.raw_message_attributes)
        except KeyError as e:
            raise ValueError(f"SQS Message is invalid: {e.args[0]}")

    def __eq__(self, other):
        return self.message_id == other.message_id

    @property
    def event(self):
        return self.message_attributes[settings.SNS_DOMAIN_EVENT_KEY]

    def checksum_body(self):
        return hashlib.md5(self.raw_body.encode('utf-8')).hexdigest() == self.md5_of_body

    @staticmethod
    def _unpack_message_attributes(message_attributes):

        _message_attributes = {}


        for attribute, attribute_value in message_attributes.items():
            data_type = attribute_value['DataType'].split('.', 1)[0]

            if data_type == "Number":
                data_type = "String"

            _message_attributes.update({attribute: attribute_value[f'{data_type}Value']})

        return _message_attributes