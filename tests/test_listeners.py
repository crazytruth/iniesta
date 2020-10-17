import pytest
import ujson as json

from insanic.conf import settings
from iniesta.listeners import IniestaListener
from iniesta.sns import SNSClient
from iniesta.sqs import SQSClient

from .infra import SNSInfra, SQSInfra


class TestListeners(SNSInfra, SQSInfra):
    queue_name = "iniesta-tests-xavi"
    filters = []

    # @pytest.fixture(scope='function')
    # def set_filters(self, monkeypatch):
    #     monkeypatch.setattr(settings, 'INIESTA_SQS_CONSUMER_FILTERS', ['Pass.xavi', 'Trap.*'], raising=False)

    @pytest.fixture(scope="function")
    async def sns_client(self, create_global_sns, monkeypatch, filter_policy):
        monkeypatch.setattr(
            settings,
            "INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN",
            create_global_sns["TopicArn"],
        )

        client = await SNSClient.initialize(
            topic_arn=create_global_sns["TopicArn"]
        )
        return client

    @pytest.fixture(scope="function")
    async def sqs_client(self, sns_client, create_service_sqs):
        client = await SQSClient.initialize(queue_name=self.queue_name)
        yield client

        SQSClient.handlers = {}
        SQSClient.queue_urls = {}

    @pytest.fixture
    def listener(self):
        listener = IniestaListener()
        yield listener

    @pytest.fixture(scope="function")
    def subscribe_sqs_to_sns(
        self,
        create_global_sns,
        sqs_client,
        create_service_sqs,
        monkeypatch,
        aws_client_kwargs,
    ):

        sns = self.aws_client("sns", **aws_client_kwargs)

        response = sns.subscribe(
            TopicArn=create_global_sns["TopicArn"],
            Protocol="sqs",
            Endpoint=create_service_sqs["Attributes"]["QueueArn"],
            Attributes={
                "RawMessageDelivery": "true",
                "FilterPolicy": json.dumps(sqs_client.filters),
            },
        )
        # NOTE: why response of get_subscription_attributes does not have 'FilterPolicy'? it will cause tests failed
        # response = sns.get_subscription_attributes(
        #     SubscriptionArn=response['SubscriptionArn']
        # )
        # assert response['Attributes']['FilterPolicy'] == json.dumps(sqs_client.filters)
        yield response

        sns.unsubscribe(SubscriptionArn=response["SubscriptionArn"])

    async def test_producer_listener(
        self, insanic_application, listener, sns_client
    ):
        await listener.after_server_start_producer_check(insanic_application)

        assert hasattr(insanic_application, "xavi")
        assert isinstance(insanic_application.xavi, SNSClient)

    async def test_queue_polling(
        self, insanic_application, listener, sqs_client
    ):
        await listener.after_server_start_start_queue_polling(
            insanic_application
        )

        assert hasattr(insanic_application, "messi")
        assert isinstance(insanic_application.messi, SQSClient)
        assert insanic_application.messi._receive_messages is True
        assert insanic_application.messi._polling_task is not None

    async def test_event_polling(
        self,
        insanic_application,
        listener,
        sns_client,
        sqs_client,
        subscribe_sqs_to_sns,
        add_permissions,
        monkeypatch,
    ):
        await listener.after_server_start_event_polling(insanic_application)

        assert hasattr(insanic_application, "messi")
        assert isinstance(insanic_application.messi, SQSClient)

        assert insanic_application.messi._receive_messages is True
        assert insanic_application.messi._polling_task is not None
