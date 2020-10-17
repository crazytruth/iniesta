from typing import Any, Union

import ujson as json

from collections import UserDict

from insanic.conf import settings


class MessageAttributes(UserDict):
    """
    Base class for :code:`SQSMessage` and :code:`SNSMessage`
    because both messages uses message attributes.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self["MessageAttributes"] = {}

    @property
    def message_attributes(self) -> dict:
        return self.get("MessageAttributes", {})

    def add_event(self, value: str, *, raw: bool = False):
        """
        Adds the event to the message to be sent.
        """
        if not isinstance(value, str):
            raise ValueError("Event must be a string.")

        if not raw and not value.endswith(f".{settings.get('SERVICE_NAME')}"):
            value = ".".join([value, settings.SERVICE_NAME])

        self.add_string_attribute(settings.INIESTA_SNS_EVENT_KEY, value)

    def add_attribute(self, attribute_name: str, attribute_value: Any) -> None:
        """
        Adds an attribute depending on value type.

        :raises ValueError: If the value is not a supported type.
        """
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

    def add_string_attribute(
        self, attribute_name: str, attribute_value: str
    ) -> None:
        """
        Adds a string attribute to the message.

        :raises ValueError: If the value is not a string.
        """
        if not isinstance(attribute_value, str):
            raise ValueError("Value is not a string.")

        self["MessageAttributes"].update(
            {
                attribute_name: {
                    "DataType": "String",
                    "StringValue": attribute_value,
                }
            }
        )

    def add_number_attribute(
        self, attribute_name: str, attribute_value: Union[int, float]
    ) -> None:
        """
        Adds a number attribute to the message.

        :raises ValueError: If the value is not an int or a float.
        """
        if not isinstance(attribute_value, (int, float)):
            raise ValueError("Value is not a number.")

        self["MessageAttributes"].update(
            {
                attribute_name: {
                    "DataType": "Number",
                    "StringValue": str(attribute_value),
                }
            }
        )

    def add_list_attribute(
        self, attribute_name: str, attribute_value: Union[list, tuple]
    ) -> None:
        """
        Adds a list attribute to the message.

        :raises ValueError: If the value is not a list or tuple type.
        """
        if not isinstance(attribute_value, (list, tuple)):
            raise ValueError("Value is not a list or tuple.")

        self["MessageAttributes"].update(
            {
                attribute_name: {
                    "DataType": "String.Array",
                    "StringValue": json.dumps(attribute_value),
                }
            }
        )

    def add_binary_attribute(self, attribute_name: str, attribute_value: bytes):
        """
        Adds a binary attribute.

        :raises ValueError: If the value is not bytes
        """
        if not isinstance(attribute_value, bytes):
            raise ValueError("Value is not bytes.")

        self["MessageAttributes"].update(
            {
                attribute_name: {
                    "DataType": "Binary",
                    "BinaryValue": attribute_value,
                }
            }
        )
