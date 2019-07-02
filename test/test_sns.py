import botocore
import pytest
import ujson as json

from insanic.conf import settings
from insanic.responses import json_response
from insanic.views import InsanicView

from iniesta.sessions import BotoSession
from iniesta.sns import SNSClient, SNSMessage

from .infra import SNSInfra


class TestSNSMessage:

    def test_sns_message_initialize(self):
        message = SNSMessage()
        assert message.message == ""

        message2 = SNSMessage("hello")
        assert message2.message == "hello"

    def test_add_event(self):
        message = SNSMessage()
        message.add_event("Awesome!")

        assert settings.INIESTA_SNS_EVENT_KEY in message.message_attributes
        assert message.message_attributes[settings.INIESTA_SNS_EVENT_KEY]['StringValue'] == "Awesome!.xavi"

    @pytest.mark.parametrize("test_value", (
        "",
        "b"
    ))
    def test_add_string_attribute(self, test_value):
        message = SNSMessage()
        message.add_string_attribute("test", test_value)

        assert "test" in message.message_attributes
        assert "DataType" in message.message_attributes['test']
        assert message.message_attributes['test']['DataType'] == "String"
        assert "StringValue" in message.message_attributes['test']
        assert message.message_attributes['test']['StringValue'] == test_value

    @pytest.mark.parametrize("test_value", (
        1,
        2.34
    ))
    def test_add_number_attribute(self, test_value):
        message = SNSMessage()
        message.add_number_attribute("test", test_value)

        assert "test" in message.message_attributes
        assert "DataType" in message.message_attributes['test']
        assert message.message_attributes['test']['DataType'] == "Number"
        assert "StringValue" in message.message_attributes['test']
        assert message.message_attributes['test']['StringValue'] == str(test_value)

    @pytest.mark.parametrize("test_value", (
        [],
        [1, ],
        (),
        (1, ),
    ))
    def test_add_list_attribute(self, test_value):
        message = SNSMessage()
        message.add_list_attribute("test", test_value)

        assert "test" in message.message_attributes
        assert "DataType" in message.message_attributes['test']
        assert message.message_attributes['test']['DataType'] == "String.Array"
        assert "StringValue" in message.message_attributes['test']
        assert message.message_attributes['test']['StringValue'] == json.dumps(test_value)

    @pytest.mark.parametrize("test_value", (
        b"",
        b"a"
    ))
    def test_add_binary_attribute(self, test_value):
        message = SNSMessage()
        message.add_binary_attribute("test", test_value)

        assert "test" in message.message_attributes
        assert "DataType" in message.message_attributes['test']
        assert message.message_attributes['test']['DataType'] == "Binary"
        assert "BinaryValue" in message.message_attributes['test']
        assert message.message_attributes['test']['BinaryValue'] == test_value

    @pytest.mark.parametrize("test_value, expected_data_type, expected_value_key", (
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
    ))
    def test_add_attribute(self, test_value, expected_data_type, expected_value_key):
        message = SNSMessage()
        message.add_attribute("test", test_value)

        assert "test" in message.message_attributes
        assert "DataType" in message.message_attributes['test']
        assert message.message_attributes['test']['DataType'] == expected_data_type
        assert expected_value_key in message.message_attributes['test']

        if expected_data_type == "String.Array":
            test_value = json.dumps(test_value)
        elif expected_data_type == "Number":
            test_value = str(test_value)

        assert message.message_attributes['test'][expected_value_key] == test_value


    @pytest.mark.parametrize('error_value', (
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
        b"d"
    ))
    def test_add_string_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_string_attribute("error", error_value)

        assert "error" not in message.message_attributes

    @pytest.mark.parametrize('error_value', (
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
        b"d"
    ))
    def test_add_number_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_number_attribute("error", error_value)

        assert "error" not in message.message_attributes

    @pytest.mark.parametrize('error_value', (
        0,
        1,
        0.0,
        2.34,
        "",
        "a",
        {},
        {"a": "b"},
        b"",
        b"d"
    ))
    def test_add_list_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_list_attribute("error", error_value)

        assert "error" not in message.message_attributes

    @pytest.mark.parametrize('error_value', (
        "",
        "a",
        0,
        1,
        0.0,
        2.34,
        "",
        "a",
        {},
        {"a": "b"},
    ))
    def test_add_binary_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_binary_attribute("error", error_value)

        assert "error" not in message.message_attributes

    @pytest.mark.parametrize('error_value', (
        {},
        {"a": "b"},
    ))
    def test_add_attribute_error(self, error_value):
        message = SNSMessage()

        with pytest.raises(ValueError):
            message.add_binary_attribute("error", error_value)

        assert "error" not in message.message_attributes


class TestSNSClient(SNSInfra):


    async def test_client_initialize(self, start_local_aws, create_global_sns, sns_endpoint_url):

        client = await SNSClient.initialize(
            topic_arn=create_global_sns['TopicArn'])
        assert client.topic_arn == create_global_sns['TopicArn']


    async def test_client_create_message(self, start_local_aws, create_global_sns, sns_endpoint_url):
        client = await SNSClient.initialize(
            topic_arn=create_global_sns['TopicArn']
        )

        response = client.create_message(
            event="SomethingAwesomeHappened",
            message="Great Success!", value="Something")

        assert response is not None
        assert response.client == client
        assert isinstance(response, SNSMessage)
        # assert 'MessageId' in response
        # assert response['MessageId'] is not None

    async def test_client_topic_doesnt_exist(self, start_local_aws, sns_endpoint_url):

        with pytest.raises(botocore.exceptions.ClientError):
            client = await SNSClient.initialize(
                topic_arn="asdasda")

    async def test_list_subscriptions_empty(self, start_local_aws, create_global_sns, sns_endpoint_url):

        client = await SNSClient.initialize(
            topic_arn=create_global_sns['TopicArn']
        )

        subscriptions = [s async for s in client.list_subscriptions_by_topic()]

        assert len(subscriptions) == 0

    async def test_list_subscriptions_with_existing(self, start_local_aws, create_global_sns,
                                                    create_service_sqs, create_sqs_subscription,
                                                    sns_endpoint_url):

        client = await SNSClient.initialize(
            topic_arn=create_global_sns['TopicArn']
        )

        subscriptions = [s async for s in client.list_subscriptions_by_topic()]

        assert len(subscriptions) == 1

        assert subscriptions[0]['Protocol'] == 'sqs'
        assert subscriptions[0]['Endpoint'] == create_service_sqs['Attributes']['QueueArn']

    async def test_get_subscription_attributes(self, start_local_aws, create_global_sns,
                                               create_service_sqs, create_sqs_subscription, sns_endpoint_url):

        """
        Actual attributes response
        {
            'Owner': '120387605022',
            'RawMessageDelivery': 'false',
            'FilterPolicy': '{"iniesta_pass":["hello",{"prefix":"Request"}]}',
            'TopicArn': 'arn:aws:sns:ap-northeast-1:120387605022:test-test-global',
            'Endpoint': 'arn:aws:sqs:ap-northeast-1:120387605022:iniesta-test-test',
            'Protocol': 'sqs',
            'PendingConfirmation': 'false', 'ConfirmationWasAuthenticated': 'true',
            'SubscriptionArn': 'arn:aws:sns:ap-northeast-1:120387605022:test-test-global:cd591f81-c223-4cf8-828d-6fbbce3f66f3'
        }


        :param start_local_aws:
        :param create_global_sns:
        :param create_service_sqs:
        :param create_sqs_subscription:
        :param sns_endpoint_url:
        :return:
        """

        client = await SNSClient.initialize(
            topic_arn=create_global_sns['TopicArn']
        )

        subscriptions = [s async for s in client.list_subscriptions_by_topic()]

        subscription = subscriptions[0]

        attributes = await client.get_subscription_attributes(subscription['SubscriptionArn'])

        assert attributes['Attributes']['TopicArn'] == create_global_sns['TopicArn']
        assert attributes['Attributes']['Protocol'] == 'sqs'

    @pytest.fixture()
    async def insanic_application_with_event_polling(self, monkeypatch, insanic_application, create_global_sns, filter_policy):
        monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN', create_global_sns['TopicArn'],
                            raising=False)
        from iniesta import Iniesta
        Iniesta.init_producer(insanic_application)

        client = await SNSClient.initialize(
            topic_arn=create_global_sns['TopicArn']
        )

        class TestView(InsanicView):
            permission_classes = []

            @client.publish_event(event='testEvent')
            def get(self, request, *args, **kwargs):
                return json_response({"help": "me"})

        insanic_application.add_route(TestView.as_view(), '/test/event/')

        return insanic_application

    def test_publish_event_decorator(self, start_local_aws, create_global_sns, sns_endpoint_url,
                                     insanic_application_with_event_polling, monkeypatch):
        BotoSession.session = None

        errors = []

        async def mock_publish(message):

            try:
                assert message.event == "testEvent.xavi"
            except AssertionError as e:
                errors.append(e)
                raise

            try:
                assert json.loads(message.message) == {"help": "me"}
            except AssertionError as e:
                errors.append(e)
                raise

        monkeypatch.setattr(SNSMessage, 'publish', mock_publish)

        request, response = insanic_application_with_event_polling.test_client.get('/test/event/')
        assert response.status == 200
        assert response.json == {"help": "me"}

        if errors:
            raise errors[0]


    def test_publish_event_decorator_even_if_publishing_error(self, start_local_aws, create_global_sns,
                                                              sns_endpoint_url, insanic_application_with_event_polling,
                                                              monkeypatch):

        BotoSession.session = None

        async def mock_publish(message):
            raise Exception("AAAAHHHHHH SOMETHING WENT WRONG!")

        monkeypatch.setattr(SNSMessage, 'publish', mock_publish)

        request, response = insanic_application_with_event_polling.test_client.get('/test/event/')
        assert response.status == 200
        assert response.json == {"help": "me"}