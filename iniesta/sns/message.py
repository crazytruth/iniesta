import ujson as json
from insanic.conf import settings

from iniesta.messages import MessageAttributes


class SNSMessage(MessageAttributes):

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

