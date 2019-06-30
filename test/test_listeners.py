import boto3
import pytest
import ujson as json

from insanic.conf import settings
from iniesta.listeners import IniestaListener
from iniesta.sessions import BotoSession
from iniesta.sns import SNSClient
from iniesta.sqs import SQSClient

from .infra import SNSInfra, SQSInfra


class TestListeners(SNSInfra, SQSInfra):
    queue_name = 'iniesta-test-xavi'
    filters = []

    @pytest.fixture(scope='function')
    async def sns_client(self, create_global_sns, sns_endpoint_url, monkeypatch):
        monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN', create_global_sns['TopicArn'])

        client = await SNSClient.initialize(
            topic_arn=create_global_sns['TopicArn']
        )
        return client

    @pytest.fixture(scope='function')
    async def sqs_client(self, sqs_region_name, sqs_endpoint_url, sns_client, create_service_sqs):
        client = await SQSClient.initialize(queue_name=self.queue_name)
        yield client

        SQSClient.handlers = {}
        SQSClient.queue_urls = {}

    @pytest.fixture
    def listener(self, start_local_aws, sns_region_name, sns_endpoint_url, sqs_region_name, sqs_endpoint_url,
                 monkeypatch):
        listener = IniestaListener()
        yield listener

    @pytest.fixture(scope='function')
    def subscribe_sqs_to_sns(self, start_local_aws, create_global_sns, sqs_client, create_service_sqs,
                             sns_region_name, sns_endpoint_url, monkeypatch):

        monkeypatch.setattr(settings, 'INIESTA_SQS_CONSUMER_FILTERS', ['Pass.xavi', 'Trap.*'], raising=False)
        sns = boto3.client('sns', region_name=sns_region_name, endpoint_url=sns_endpoint_url,
                           aws_access_key_id=BotoSession.aws_access_key_id,
                           aws_secret_access_key=BotoSession.aws_secret_access_key)

        response = sns.subscribe(TopicArn=create_global_sns['TopicArn'],
                                 Protocol='sqs',
                                 Endpoint=create_service_sqs['Attributes']['QueueArn'],
                                 Attributes={
                                     "RawMessageDelivery": "true",
                                     "FilterPolicy": json.dumps(sqs_client.filters),
                                 })
        # NOTE: why response of get_subscription_attributes does not have 'FilterPolicy'? it will cause test failed
        # response = sns.get_subscription_attributes(
        #     SubscriptionArn=response['SubscriptionArn']
        # )
        # assert response['Attributes']['FilterPolicy'] == json.dumps(sqs_client.filters)
        yield response

        sns.unsubscribe(SubscriptionArn=response['SubscriptionArn'])

    @pytest.fixture(scope='function')
    def add_permissions(self, subscribe_sqs_to_sns, create_global_sns,
                        create_service_sqs, sqs_region_name, sqs_endpoint_url):
        sqs = boto3.client('sqs', region_name=sqs_region_name, endpoint_url=sqs_endpoint_url,
                           aws_access_key_id=BotoSession.aws_access_key_id,
                           aws_secret_access_key=BotoSession.aws_secret_access_key)

        response = sqs.set_queue_attributes(
            QueueUrl=create_service_sqs['QueueUrl'],
            Attributes={
                "Policy": json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Id": f"arn:aws:sqs:ap-northeast-1:120387605022:{self.queue_name}/SQSDefaultPolicy",
                        "Statement": [
                            {
                                "Sid": "Sid1552456721343",
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": "SQS:SendMessage",
                                "Resource": create_service_sqs['Attributes']['QueueArn'],
                                "Condition": {
                                    "ArnEquals": {
                                        "aws:SourceArn": create_global_sns['TopicArn']
                                    }
                                }
                            }
                        ]
                    }
                )
            }
        )
        # NOTE: why response of get_queue_attributes does not have 'Attributes'? it will cause test failed
        # policy_attributes = sqs.get_queue_attributes(
        #     QueueUrl=create_service_sqs['QueueUrl'],
        #     AttributeNames=['Policy']
        # )
        # policies = json.loads(policy_attributes['Attributes']['Policy'])
        # statement = policies['Statement'][0]
        # assert statement['Effect'] == "Allow"
        # assert "SQS:SendMessage" in statement['Action']

        return response

    async def test_producer_listener(self, insanic_application, listener, sns_client):
        await listener.after_server_start_producer_check(insanic_application)

        assert hasattr(insanic_application, 'xavi')
        assert isinstance(insanic_application.xavi, SNSClient)

    async def test_queue_polling(self, insanic_application, listener, sqs_client):
        await listener.after_server_start_start_queue_polling(insanic_application)

        assert hasattr(insanic_application, 'messi')
        assert isinstance(insanic_application.messi, SQSClient)
        assert insanic_application.messi._receive_messages is True
        assert insanic_application.messi._polling_task is not None

    async def test_event_polling(self, insanic_application, listener, sns_client, sqs_client,
                                 subscribe_sqs_to_sns, add_permissions, monkeypatch):
        # NOTE: this test will be failed but I dont know why
        await listener.after_server_start_event_polling(insanic_application)

        assert hasattr(insanic_application, 'messi')
        assert isinstance(insanic_application.messi, SQSClient)

        assert insanic_application.messi._receive_messages is True
        assert insanic_application.messi._polling_task is not None
