import ujson as json

from collections import UserDict

from insanic.conf import settings


class SNSMessage(UserDict):

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
            raise ValueError("Message must be a string.")

        self['Message'] = value

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

    @property
    def message_attributes(self):
        return self.get('MessageAttributes', {})

    def add_event(self, value):
        if not isinstance(value, str):
            raise ValueError("Event must be a string.")

        if not value.endswith(f".{settings.SERVICE_NAME}"):
            value = ".".join([value, settings.SERVICE_NAME])

        self.add_string_attribute(settings.INIESTA_SNS_EVENT_KEY, value)

    def add_attribute(self, attribute_name, attribute_value):
        if isinstance(attribute_value, str):
            self.add_string_attribute(attribute_name, attribute_value)
        elif isinstance(attribute_value, (int, float)):
            self.add_number_attribute(attribute_name, attribute_value)
        elif isinstance(attribute_value, (list, tuple)):
            self.add_list_attribute(attribute_name, attribute_value)
        elif isinstance(attribute_value, bytes):
            self.add_binary_attribute(attribute_name, attribute_value)
        else:
            raise ValueError("Invalid type.")

    def add_string_attribute(self, attribute_name, attribute_value):
        if not isinstance(attribute_value, str):
            raise ValueError("Value is not a string.")

        self['MessageAttributes'].update({attribute_name: {
            "DataType": "String",
            "StringValue": attribute_value
        }})

    def add_number_attribute(self, attribute_name, attribute_value):
        if not isinstance(attribute_value, (int, float)):
            raise ValueError("Value is not a string.")

        self['MessageAttributes'].update({attribute_name: {
            "DataType": "Number",
            "StringValue": str(attribute_value)
        }})

    def add_list_attribute(self, attribute_name, attribute_value):
        if not isinstance(attribute_value, (list, tuple)):
            raise ValueError("Value is not a list or tuple.")

        self['MessageAttributes'].update({attribute_name: {
            "DataType": "String.Array",
            "StringValue": json.dumps(attribute_value)
        }})

    def add_binary_attribute(self, attribute_name, attribute_value):
        if not isinstance(attribute_value, bytes):
            raise ValueError("Value is not a list or tuple.")

        self['MessageAttributes'].update({attribute_name: {
            "DataType": "Binary",
            "BinaryValue": attribute_value
        }})
