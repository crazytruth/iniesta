import botocore
import pytest
import ujson as json

from insanic.conf import settings

from iniesta import Iniesta
from iniesta.sessions import BotoSession


class InfraBase:
    def aws_client(self, service, **kwargs):
        return botocore.session.get_session().create_client(service, **kwargs)

    @pytest.fixture(autouse=True)
    def load_configs(self):
        Iniesta.load_config(settings)

    @pytest.fixture(autouse=True)
    def set_endpoint_on_settings(self, monkeypatch, moto_endpoint_url):

        monkeypatch.setattr(
            settings,
            "INIESTA_SNS_ENDPOINT_URL",
            moto_endpoint_url,
            raising=False,
        )
        monkeypatch.setattr(
            settings,
            "INIESTA_SQS_ENDPOINT_URL",
            moto_endpoint_url,
            raising=False,
        )
        monkeypatch.setattr(
            settings,
            "INIESTA_STS_ENDPOINT_URL",
            moto_endpoint_url,
            raising=False,
        )

    @pytest.fixture(scope="module")
    def moto_endpoint_url(self):
        # return "http://localhost:5000"
        return "http://localhost:4566"

    @pytest.fixture(autouse=True)
    def set_service_name(self, monkeypatch):
        monkeypatch.setattr(settings, "SERVICE_NAME", "xavi")

    @pytest.fixture(scope="module")
    def aws_client_kwargs(self, moto_endpoint_url):
        return dict(
            endpoint_url=moto_endpoint_url,
            aws_access_key_id=BotoSession.aws_access_key_id,
            aws_secret_access_key=BotoSession.aws_secret_access_key,
            region_name=BotoSession.aws_default_region,
        )


class SNSInfra(InfraBase):
    queue_name = None
    topic_name = None

    @pytest.fixture(scope="module", autouse=True)
    def queue_name(self, module_id):
        self.queue_name = f"iniesta-tests-tests-{module_id}"
        yield
        self.queue_name = None

    @pytest.fixture(scope="module", autouse=True)
    def topic_name(self, module_id):
        self.topic_name = f"tests-tests-global-{module_id}"
        yield
        self.topic_name = None

    @pytest.fixture()
    def filter_policy(self, monkeypatch):
        monkeypatch.setattr(
            settings,
            "INIESTA_SQS_CONSUMER_FILTERS",
            ["hello.iniesta", "Request.*"],
            raising=False,
        )
        return {
            settings.INIESTA_SNS_EVENT_KEY: [
                "hello.iniesta",
                {"prefix": "Request."},
            ]
        }

    @pytest.fixture(scope="module")
    def create_global_sns(self, aws_client_kwargs):

        sns = self.aws_client("sns", **aws_client_kwargs)
        response = sns.create_topic(Name=self.topic_name)
        yield response
        sns.delete_topic(TopicArn=response["TopicArn"])

    @pytest.fixture(scope="module")
    def create_service_sqs(self, session_id, aws_client_kwargs):

        sqs = self.aws_client("sqs", **aws_client_kwargs)

        # template for queue name is `iniesta-{environment}-{service_name}
        response = sqs.create_queue(QueueName=self.queue_name)

        queue_attributes = sqs.get_queue_attributes(
            QueueUrl=response["QueueUrl"], AttributeNames=["QueueArn"]
        )

        response.update(queue_attributes)

        yield response

        sqs.delete_queue(QueueUrl=response["QueueUrl"])

    @pytest.fixture(scope="function")
    def create_sqs_subscription(
        self,
        create_global_sns,
        create_service_sqs,
        filter_policy,
        aws_client_kwargs,
    ):
        sns = self.aws_client("sns", **aws_client_kwargs)

        response = sns.subscribe(
            TopicArn=create_global_sns["TopicArn"],
            Protocol="sqs",
            Endpoint=create_service_sqs["Attributes"]["QueueArn"],
            Attributes={
                "FilterPolicy": json.dumps(filter_policy),
                "RawMessageDelivery": "true",
            },
        )
        yield response

        sns.unsubscribe(SubscriptionArn=response["SubscriptionArn"])


class SQSInfra(InfraBase):
    queue_name = "iniesta-tests-tests"

    @pytest.fixture(scope="module")
    def create_service_sqs(self, session_id, aws_client_kwargs):
        sqs = self.aws_client("sqs", **aws_client_kwargs)

        # template for queue name is `iniesta-{environment}-{service_name}
        while True:
            try:
                response = sqs.create_queue(QueueName=self.queue_name)
            except sqs.exceptions.QueueDeletedRecently:
                import time

                time.sleep(15)
            else:
                break

        queue_attributes = sqs.get_queue_attributes(
            QueueUrl=response["QueueUrl"], AttributeNames=["QueueArn"]
        )

        response.update(queue_attributes)

        yield response

        sqs.delete_queue(QueueUrl=response["QueueUrl"])

    @pytest.fixture(scope="function")
    def add_permissions(
        self,
        create_sqs_subscription,
        create_global_sns,
        create_service_sqs,
        aws_client_kwargs,
    ):

        sqs = self.aws_client("sqs", **aws_client_kwargs)

        response = sqs.set_queue_attributes(
            QueueUrl=create_service_sqs["QueueUrl"],
            Attributes={
                "Policy": json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Id": f"{create_service_sqs['Attributes']['QueueArn']}/SQSDefaultPolicy",
                        "Statement": [
                            {
                                "Sid": "Sid1552456721343",
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": "SQS:SendMessage",
                                "Resource": create_service_sqs["Attributes"][
                                    "QueueArn"
                                ],
                                "Condition": {
                                    "ArnEquals": {
                                        "aws:SourceArn": create_global_sns[
                                            "TopicArn"
                                        ]
                                    }
                                },
                            }
                        ],
                    }
                )
            },
        )
        return response
