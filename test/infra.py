import boto3
import pytest
import ujson as json

from localstack.services import infra

from insanic.conf import settings

from iniesta import Iniesta
from iniesta import config
from iniesta.sessions import BotoSession

RUN_LOCAL = True


class InfraBase:

    run_local = RUN_LOCAL

    @pytest.fixture(autouse=True)
    def load_configs(self):
        Iniesta.load_config(settings)


    @pytest.fixture(autouse=True)
    def set_service_name(self, monkeypatch):
        monkeypatch.setattr(settings, 'SERVICE_NAME', 'xavi')

    @pytest.fixture(scope='module')
    def sns_endpoint_url(self, start_local_aws):
        return start_local_aws.config.TEST_SNS_URL if self.run_local else None

    @pytest.fixture(scope='module')
    def sqs_endpoint_url(self, start_local_aws):
        return start_local_aws.config.TEST_SQS_URL if self.run_local else None

    @pytest.fixture(scope='module')
    def sts_endpoint_url(self, start_local_aws):
        return start_local_aws.config.TEST_STS_URL if self.run_local else None

    @pytest.fixture(scope="module")
    def start_local_aws(self):
        if self.run_local:
            infra.start_infra(asynchronous=True, apis=['sns', 'sqs'])
            yield infra
            infra.stop_infra()
        else:
            yield None


class SNSInfra(InfraBase):

    queue_name = 'iniesta-test-test'

    @pytest.fixture()
    def filter_policy(self, monkeypatch):
        monkeypatch.setattr(settings, "INIESTA_SQS_CONSUMER_FILTERS", ['hello.iniesta', "Request.*"],
                            raising=False)

        return {
            settings.INIESTA_SNS_EVENT_KEY: ["hello.iniesta", {"prefix": "Request."}]
        }


    @pytest.fixture(scope="module")
    def create_global_sns(self, start_local_aws, sns_endpoint_url):
        sns = boto3.client('sns',
                           endpoint_url=sns_endpoint_url
                           )
        response = sns.create_topic(Name="test-test-global")
        yield response
        sns.delete_topic(TopicArn=response['TopicArn'])

    @pytest.fixture(scope='module')
    def create_service_sqs(self, start_local_aws, sqs_endpoint_url, session_id):
        sqs = boto3.client('sqs', endpoint_url=sqs_endpoint_url)

        # template for queue name is `iniesta-{environment}-{service_name}
        response = sqs.create_queue(QueueName=self.queue_name)

        queue_attributes = sqs.get_queue_attributes(
            QueueUrl=response['QueueUrl'],
            AttributeNames=['QueueArn']
        )

        response.update(queue_attributes)

        yield response

        sqs.delete_queue(QueueUrl=response['QueueUrl'])

    @pytest.fixture(scope='function')
    def create_sqs_subscription(self, start_local_aws, create_global_sns,
                                create_service_sqs, sns_endpoint_url, filter_policy):
        sns = boto3.client('sns', endpoint_url=sns_endpoint_url)

        response = sns.subscribe(TopicArn=create_global_sns['TopicArn'],
                                 Protocol='sqs',
                                 Endpoint=create_service_sqs['Attributes']['QueueArn'],
                                 Attributes={
                                     "FilterPolicy": json.dumps(filter_policy),
                                     "RawMessageDelivery": "true"
                                 })
        yield response

        sns.unsubscribe(SubscriptionArn=response['SubscriptionArn'])


class SQSInfra(InfraBase):

    queue_name = 'iniesta-test-test'

    @pytest.fixture(scope='module')
    def create_service_sqs(self, start_local_aws, sqs_endpoint_url, session_id):
        sqs = boto3.client('sqs', endpoint_url=sqs_endpoint_url)

        # template for queue name is `iniesta-{environment}-{service_name}
        while True:
            try:
                response = sqs.create_queue(QueueName=self.queue_name)
            except sqs.exceptions.QueueDeletedRecently as e:
                import time
                time.sleep(15)
            else:
                break

        queue_attributes = sqs.get_queue_attributes(
            QueueUrl=response['QueueUrl'],
            AttributeNames=['QueueArn']
        )

        response.update(queue_attributes)

        yield response

        sqs.delete_queue(QueueUrl=response['QueueUrl'])


    @pytest.fixture(scope='function')
    def add_permissions(self, create_sqs_subscription, create_global_sns,
                        create_service_sqs, sqs_endpoint_url):

        sqs = boto3.client('sqs', endpoint_url=sqs_endpoint_url)

        response = sqs.set_queue_attributes(
            QueueUrl=create_service_sqs['QueueUrl'],
            Attributes = {
                "Policy": json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Id": "arn:aws:sqs:ap-northeast-1:120387605022:iniesta-test-test/SQSDefaultPolicy",
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


        return response
