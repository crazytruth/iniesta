import botocore
import pytest
import ujson as json

from sanic.response import json as json_response

from insanic.conf import settings
from insanic.views import InsanicView

from iniesta.sessions import BotoSession
from iniesta.sns import SNSClient, SNSMessage

from .infra import SNSInfra


class TestSNSClient(SNSInfra):
    async def test_client_initialize(self, create_global_sns):

        client = await SNSClient.initialize(
            topic_arn=create_global_sns["TopicArn"]
        )
        assert client.topic_arn == create_global_sns["TopicArn"]

    async def test_client_create_message(self, create_global_sns):
        client = await SNSClient.initialize(
            topic_arn=create_global_sns["TopicArn"]
        )

        response = client.create_message(
            event="SomethingAwesomeHappened",
            message="Great Success!",
            value="Something",
        )

        assert response is not None
        assert response.client == client
        assert isinstance(response, SNSMessage)
        # assert 'MessageId' in response
        # assert response['MessageId'] is not None

    async def test_client_topic_doesnt_exist(self):

        with pytest.raises(botocore.exceptions.ClientError):
            await SNSClient.initialize(topic_arn="asdasda")

    async def test_list_subscriptions_empty(self, create_global_sns):

        client = await SNSClient.initialize(
            topic_arn=create_global_sns["TopicArn"]
        )

        subscriptions = [s async for s in client.list_subscriptions_by_topic()]

        assert len(subscriptions) == 0

    async def test_list_subscriptions_with_existing(
        self, create_global_sns, create_service_sqs, create_sqs_subscription,
    ):

        client = await SNSClient.initialize(
            topic_arn=create_global_sns["TopicArn"]
        )

        subscriptions = [s async for s in client.list_subscriptions_by_topic()]

        assert len(subscriptions) == 1

        assert subscriptions[0]["Protocol"] == "sqs"
        assert (
            subscriptions[0]["Endpoint"]
            == create_service_sqs["Attributes"]["QueueArn"]
        )

    async def test_get_subscription_attributes(
        self, create_global_sns, create_service_sqs, create_sqs_subscription,
    ):

        """
        Actual attributes response
        {
            'Owner': '120387605022',
            'RawMessageDelivery': 'false',
            'FilterPolicy': '{"iniesta_pass":["hello",{"prefix":"Request"}]}',
            'TopicArn': 'arn:aws:sns:ap-northeast-1:120387605022:tests-tests-global',
            'Endpoint': 'arn:aws:sqs:ap-northeast-1:120387605022:iniesta-tests-tests',
            'Protocol': 'sqs',
            'PendingConfirmation': 'false', 'ConfirmationWasAuthenticated': 'true',
            'SubscriptionArn': 'arn:aws:sns:ap-northeast-1:120387605022:tests-tests-global:cd591f81-c223-4cf8-828d-6fbbce3f66f3'
        }

        :param create_global_sns:
        :param create_service_sqs:
        :param create_sqs_subscription:
        :return:
        """

        client = await SNSClient.initialize(
            topic_arn=create_global_sns["TopicArn"]
        )

        subscriptions = [s async for s in client.list_subscriptions_by_topic()]

        subscription = subscriptions[0]

        attributes = await client.get_subscription_attributes(
            subscription["SubscriptionArn"]
        )

        assert (
            attributes["Attributes"]["TopicArn"]
            == create_global_sns["TopicArn"]
        )
        assert attributes["Attributes"]["Protocol"] == "sqs"

    @pytest.fixture()
    async def insanic_application_with_event_polling(
        self, monkeypatch, insanic_application, create_global_sns, filter_policy
    ):
        monkeypatch.setattr(
            settings,
            "INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN",
            create_global_sns["TopicArn"],
            raising=False,
        )
        monkeypatch.setattr(
            settings,
            "INIESTA_INITIALIZATION_TYPE",
            ["SNS_PRODUCER"],
            raising=False,
        )
        from iniesta import Iniesta

        Iniesta.init_app(insanic_application)

        client = await SNSClient.initialize(
            topic_arn=create_global_sns["TopicArn"]
        )

        class TestView(InsanicView):
            permission_classes = []

            @client.publish_event(event="testEvent")
            def get(self, request, *args, **kwargs):
                return json_response({"help": "me"})

        insanic_application.add_route(TestView.as_view(), "/tests/event/")

        return insanic_application

    def test_publish_event_decorator(
        self,
        create_global_sns,
        insanic_application_with_event_polling,
        monkeypatch,
    ):
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

        monkeypatch.setattr(SNSMessage, "publish", mock_publish)

        (
            request,
            response,
        ) = insanic_application_with_event_polling.test_client.get(
            "/tests/event/"
        )
        assert response.status == 200
        assert response.json == {"help": "me"}

        if errors:
            raise errors[0]

    def test_publish_event_decorator_even_if_publishing_error(
        self,
        create_global_sns,
        insanic_application_with_event_polling,
        monkeypatch,
    ):

        BotoSession.session = None

        async def mock_publish(message):
            raise Exception("AAAAHHHHHH SOMETHING WENT WRONG!")

        monkeypatch.setattr(SNSMessage, "publish", mock_publish)

        (
            request,
            response,
        ) = insanic_application_with_event_polling.test_client.get(
            "/tests/event/"
        )
        assert response.status == 200
        assert response.json == {"help": "me"}
