import pytest
import ujson as json

from iniesta.sns.message import SNSMessage, MAX_BODY_SIZE


class TestSNSMessage:
    def test_message_init(self):
        message_string = "some random message"
        message = SNSMessage(message_string)

        assert message.message == message_string

    def test_message_property(self):
        message_string = "pass to messi!"
        message = SNSMessage("pass to xavi!")

        message.message = message_string
        assert message.message == message_string

        message_object = {"command": message_string}
        message.message = message_object
        assert message.message == json.dumps(message_object)

    def test_message_property_errors(self):
        message = SNSMessage("pass to xavi!")

        message_error = object()
        with pytest.raises(TypeError):
            message.message = message_error

        message_too_long = "a" * (MAX_BODY_SIZE + 1)
        with pytest.raises(ValueError):
            message.message = message_too_long

    def test_subject_property(self):
        subject_string = "tactics"

        message = SNSMessage()
        message.subject = subject_string

        assert message.subject == subject_string

    def test_subject_property_non_string(self):

        message = SNSMessage()

        with pytest.raises(TypeError):
            message.subject = {}

    @pytest.mark.parametrize("value", ["json", "string"])
    def test_message_structure(self, value):
        message = SNSMessage()
        message.message_structure = value

        assert message.message_structure == value

    def test_message_structure_invalid(self):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.message_structure = "invalid!"

    def test_string_message_attributes(self):
        message = SNSMessage()

        assert message.message_attributes == {}

        message.add_string_attribute("a", "b")
        assert message.message_attributes == {
            "a": {"DataType": "String", "StringValue": "b"}
        }
        message.add_attribute("c", "d")
        assert message.message_attributes == {
            "a": {"DataType": "String", "StringValue": "b"},
            "c": {"DataType": "String", "StringValue": "d"},
        }

        message.add_attribute("a", "c")
        assert message.message_attributes == {
            "a": {"DataType": "String", "StringValue": "c"},
            "c": {"DataType": "String", "StringValue": "d"},
        }

        with pytest.raises(ValueError, match="Value is not a string."):
            message.add_string_attribute("a", 1)
        with pytest.raises(ValueError, match="Value is not a string."):
            message.add_string_attribute("a", [])
        with pytest.raises(ValueError, match="Value is not a string."):
            message.add_string_attribute("a", {})
        with pytest.raises(ValueError, match="Value is not a string."):
            message.add_string_attribute("a", b"b")

    def test_number_message_attributes(self):
        message = SNSMessage()

        assert message.message_attributes == {}

        message.add_number_attribute("a", 1)
        assert message.message_attributes == {
            "a": {"DataType": "Number", "StringValue": "1"}
        }
        message.add_attribute("b", 2)
        assert message.message_attributes == {
            "a": {"DataType": "Number", "StringValue": "1"},
            "b": {"DataType": "Number", "StringValue": "2"},
        }

        with pytest.raises(ValueError, match="Value is not a number."):
            message.add_number_attribute("a", "1")
        with pytest.raises(ValueError, match="Value is not a number."):
            message.add_number_attribute("a", [])
        with pytest.raises(ValueError, match="Value is not a number."):
            message.add_number_attribute("a", {})
        with pytest.raises(ValueError, match="Value is not a number."):
            message.add_number_attribute("a", b"b")

    def test_list_attribute(self):
        message = SNSMessage()

        assert message.message_attributes == {}

        message.add_list_attribute("a", [1, 2])
        assert message.message_attributes == {
            "a": {"DataType": "String.Array", "StringValue": "[1,2]"}
        }
        message.add_attribute("b", [3, 4])
        assert message.message_attributes == {
            "a": {"DataType": "String.Array", "StringValue": "[1,2]"},
            "b": {"DataType": "String.Array", "StringValue": "[3,4]"},
        }
        with pytest.raises(ValueError, match="Value is not a list or tuple."):
            message.add_list_attribute("a", "1")
        with pytest.raises(ValueError, match="Value is not a list or tuple."):
            message.add_list_attribute("a", 1)
        with pytest.raises(ValueError, match="Value is not a list or tuple."):
            message.add_list_attribute("a", {})
        with pytest.raises(ValueError, match="Value is not a list or tuple."):
            message.add_list_attribute("a", b"b")

    def test_binary_attribute(self):
        message = SNSMessage()

        assert message.message_attributes == {}

        message.add_binary_attribute("a", b"b")
        assert message.message_attributes == {
            "a": {"DataType": "Binary", "BinaryValue": b"b"}
        }
        message.add_attribute("b", b"c")
        assert message.message_attributes == {
            "a": {"DataType": "Binary", "BinaryValue": b"b"},
            "b": {"DataType": "Binary", "BinaryValue": b"c"},
        }
        with pytest.raises(ValueError, match="Value is not bytes."):
            message.add_binary_attribute("a", "1")
        with pytest.raises(ValueError, match="Value is not bytes."):
            message.add_binary_attribute("a", 1)
        with pytest.raises(ValueError, match="Value is not bytes."):
            message.add_binary_attribute("a", {})
        with pytest.raises(ValueError, match="Value is not bytes."):
            message.add_binary_attribute("a", [])

    def test_event(self, monkeypatch):
        from insanic.conf import settings

        monkeypatch.setattr(
            settings, "INIESTA_SNS_EVENT_KEY", "event", raising=False
        )

        message = SNSMessage()

        assert message.event is None

        message.add_event("do something")
        assert message.event == f"do something.{settings.SERVICE_NAME}"
        assert settings.INIESTA_SNS_EVENT_KEY in message.message_attributes

        assert (
            message.message_attributes[settings.INIESTA_SNS_EVENT_KEY][
                "StringValue"
            ]
            == "do something.xavi"
        )

    def test_add_event_error(self):

        message = SNSMessage()
        with pytest.raises(ValueError):
            message.add_event(object())

    @pytest.mark.parametrize(
        "test_value, expected_data_type, expected_value_key",
        (
            ("", "String", "StringValue"),
            ("b", "String", "StringValue"),
            (0, "Number", "StringValue"),
            (1, "Number", "StringValue"),
            (0.0, "Number", "StringValue"),
            (2.34, "Number", "StringValue"),
            ([], "String.Array", "StringValue"),
            (["a", "b"], "String.Array", "StringValue"),
            ([1, 2], "String.Array", "StringValue"),
            ((), "String.Array", "StringValue"),
            (("c", "d"), "String.Array", "StringValue"),
            ((3, 4), "String.Array", "StringValue"),
            (b"", "Binary", "BinaryValue"),
            (b"d", "Binary", "BinaryValue"),
        ),
    )
    def test_add_attribute(
        self, test_value, expected_data_type, expected_value_key
    ):
        message = SNSMessage()
        message.add_attribute("tests", test_value)

        assert "tests" in message.message_attributes
        assert "DataType" in message.message_attributes["tests"]
        assert (
            message.message_attributes["tests"]["DataType"]
            == expected_data_type
        )
        assert expected_value_key in message.message_attributes["tests"]

        if expected_data_type == "String.Array":
            test_value = json.dumps(test_value)
        elif expected_data_type == "Number":
            test_value = str(test_value)

        assert (
            message.message_attributes["tests"][expected_value_key]
            == test_value
        )

    @pytest.mark.parametrize(
        "error_value",
        (
            0,
            1,
            0.0,
            2.34,
            [],
            ["a", "b"],
            [1, 2],
            (),
            ("c", "d"),
            (3, 4),
            {},
            {"a": "b"},
            b"",
            b"d",
        ),
    )
    def test_add_string_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_string_attribute("error", error_value)

        assert "error" not in message.message_attributes

    @pytest.mark.parametrize(
        "error_value",
        (
            "",
            "a",
            [],
            ["a", "b"],
            [1, 2],
            (),
            ("c", "d"),
            (3, 4),
            {},
            {"a": "b"},
            b"",
            b"d",
        ),
    )
    def test_add_number_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_number_attribute("error", error_value)

        assert "error" not in message.message_attributes

    @pytest.mark.parametrize(
        "error_value", (0, 1, 0.0, 2.34, "", "a", {}, {"a": "b"}, b"", b"d")
    )
    def test_add_list_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_list_attribute("error", error_value)

        assert "error" not in message.message_attributes

    @pytest.mark.parametrize(
        "error_value", ("", "a", 0, 1, 0.0, 2.34, "", "a", {}, {"a": "b"},)
    )
    def test_add_binary_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_binary_attribute("error", error_value)

        assert "error" not in message.message_attributes

    @pytest.mark.parametrize("error_value", ({}, {"a": "b"},))
    def test_add_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_binary_attribute("error", error_value)

        assert "error" not in message.message_attributes
