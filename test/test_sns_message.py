import pytest
from iniesta.sns.message import SNSMessage


class TestSNSMessage:

    def test_message_init(self):
        message_string = 'some random message'
        message = SNSMessage(message_string)

        assert message.message == message_string

    def test_message_property(self):
        message_string = 'pass to messi!'
        message = SNSMessage("pass to xavi!")

        message.message = message_string
        assert message.message == message_string

    def test_subject_property(self):
        subject_string = "tactics"

        message = SNSMessage()
        message.subject = subject_string

        assert message.subject == subject_string

    @pytest.mark.parametrize('value', ['json', 'string'])
    def test_message_structure(self, value):
        message = SNSMessage()
        message.message_structure = value

        assert message.message_structure == value

    def test_string_message_attributes(self):
        message = SNSMessage()

        assert message.message_attributes == {}

        message.add_string_attribute('a', 'b')
        assert message.message_attributes == \
               {
                   "a": {"DataType": "String", "StringValue": "b"}
               }
        message.add_attribute('c', 'd')
        assert message.message_attributes == \
               {
                   "a": {"DataType": "String", "StringValue": "b"},
                   "c": {"DataType": "String", "StringValue": "d"}
               }

        message.add_attribute('a', 'c')
        assert message.message_attributes == \
               {
                   "a": {"DataType": "String", "StringValue": "c"},
                   "c": {"DataType": "String", "StringValue": "d"}
               }

        with pytest.raises(ValueError, match='Value is not a string.'):
            message.add_string_attribute('a', 1)
        with pytest.raises(ValueError, match='Value is not a string.'):
            message.add_string_attribute('a', [])
        with pytest.raises(ValueError, match='Value is not a string.'):
            message.add_string_attribute('a', {})
        with pytest.raises(ValueError, match="Value is not a string."):
            message.add_string_attribute('a', b'b')

    def test_number_message_sttributes(self):
        message = SNSMessage()

        assert message.message_attributes == {}

        message.add_number_attribute('a', 1)
        assert message.message_attributes == \
               {
                   "a": {"DataType": "Number", "StringValue": "1"}
               }
        message.add_attribute('b', 2)
        assert message.message_attributes == \
               {
                   "a": {"DataType": "Number", "StringValue": "1"},
                   "b": {"DataType": "Number", "StringValue": "2"}
               }

        with pytest.raises(ValueError, match='Value is not a number.'):
            message.add_number_attribute('a', "1")
        with pytest.raises(ValueError, match='Value is not a number.'):
            message.add_number_attribute('a', [])
        with pytest.raises(ValueError, match='Value is not a number.'):
            message.add_number_attribute('a', {})
        with pytest.raises(ValueError, match="Value is not a number."):
            message.add_number_attribute('a', b'b')

    def test_list_attribute(self):
        message = SNSMessage()

        assert message.message_attributes == {}

        message.add_list_attribute('a', [1,2])
        assert message.message_attributes == \
               {
                   "a": {"DataType": "String.Array", "StringValue": "[1,2]"}
               }
        message.add_attribute('b', [3,4])
        assert message.message_attributes == \
               {
                   "a": {"DataType": "String.Array", "StringValue": "[1,2]"},
                   "b": {"DataType": "String.Array", "StringValue": "[3,4]"}
               }
        with pytest.raises(ValueError, match="Value is not a list or tuple."):
            message.add_list_attribute('a', "1")
        with pytest.raises(ValueError, match="Value is not a list or tuple."):
            message.add_list_attribute('a', 1)
        with pytest.raises(ValueError, match="Value is not a list or tuple."):
            message.add_list_attribute('a', {})
        with pytest.raises(ValueError, match="Value is not a list or tuple."):
            message.add_list_attribute('a', b'b')

    def test_binary_attribute(self):
        message = SNSMessage()

        assert message.message_attributes == {}

        message.add_binary_attribute('a', b'b')
        assert message.message_attributes == \
               {
                   "a": {"DataType": "Binary", "BinaryValue": b'b'}
               }
        message.add_attribute('b', b'c')
        assert message.message_attributes == \
               {
                   "a": {"DataType": "Binary", "BinaryValue": b'b'},
                   "b": {"DataType": "Binary", "BinaryValue": b'c'}
               }
        with pytest.raises(ValueError, match="Value is not bytes."):
            message.add_binary_attribute('a', "1")
        with pytest.raises(ValueError, match="Value is not bytes."):
            message.add_binary_attribute('a', 1)
        with pytest.raises(ValueError, match="Value is not bytes."):
            message.add_binary_attribute('a', {})
        with pytest.raises(ValueError, match="Value is not bytes."):
            message.add_binary_attribute('a', [])

    def test_event(self, monkeypatch):
        from insanic.conf import settings
        monkeypatch.setattr(settings, 'INIESTA_SNS_EVENT_KEY', 'event', raising=False)

        message = SNSMessage()

        assert message.event is None

        message.add_event("do something")
        assert message.event == f"do something.{settings.SERVICE_NAME}"
