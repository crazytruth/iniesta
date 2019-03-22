import botocore
import pytest

from insanic import Insanic
from insanic.conf import settings
from iniesta import Iniesta, config

from .infra import SNSInfra

class InitializeFixtures:
    @pytest.fixture
    def insanic_application(self):
        app = Insanic('xavi')
        Iniesta.init_app(app)
        yield app

    @pytest.fixture
    def insanic_server(self, loop, insanic_application, test_server, monkeypatch):
        monkeypatch.setattr(settings, 'GRPC_PORT_DELTA', 1)

        return loop.run_until_complete(test_server(insanic_application))


class TestIniestaInitialize(InitializeFixtures):


    def test_plugin(self, insanic_application):

        # test for after server start listener
        for f in insanic_application.listeners['after_server_start']:
            if  f.__module__ == "iniesta.app":
                assert f.__name__ == 'after_server_start_poll_sqs_for_messages'
                break
        else:
            raise AssertionError("after_server_start listener not found")

        # test for before server stop listener
        for f in insanic_application.listeners['before_server_stop']:
            if f.__module__ == "iniesta.app":
                assert f.__name__ == 'before_server_stop_stop_polling'
                break
        else:
            raise AssertionError("before_server_stop listener not found")

        # test for if configs are all imported into insanic config
        for c in dir(config):
            if c.isupper():
                assert hasattr(settings, c)



    async def test_insanic_run_sns_not_set(self, insanic_application, test_server):
        with pytest.raises(EnvironmentError) as exc_info:
            await test_server(insanic_application)

        assert exc_info.typename == "OSError"

    @pytest.mark.parametrize("topic_arn", (
        "something wrong",
        "a:b:c:d:e:f",
        "arn:b:c:d:e:f",
        "arn:aws:sns:ap-northeast-1:e:f",
    ))
    async def test_insanic_run_bad_topic_arn(self, insanic_application, test_server,
                                             topic_arn, monkeypatch):
        monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN', topic_arn)
        with pytest.raises(botocore.exceptions.ClientError) as exc_info:
            await test_server(insanic_application)

        assert exc_info


class TestInitializeWithSNS(SNSInfra):
    queue_name = "iniesta-test-xavi"

    @pytest.fixture()
    def insanic_application(self, sns_endpoint_url, sqs_endpoint_url):

        app = Insanic("xavi")

        Iniesta.init_app(app, sns_endpoint_url=sns_endpoint_url, sqs_endpoint_url=sqs_endpoint_url)
        yield app

    @pytest.fixture(autouse=True)
    def set_global_topic_arn(self, create_global_sns, monkeypatch):
        monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN', create_global_sns['TopicArn'])

    async def test_insanic_run_with_topic_but_no_queue(self, insanic_application, test_server,
                                                       create_global_sns):
        with pytest.raises(botocore.exceptions.ClientError) as exc_info:
            await test_server(insanic_application)

        assert exc_info
        assert exc_info.typename == "QueueDoesNotExist"

    async def test_insanic_run_with_topic_and_queue_but_no_subscriptions(self, insanic_application,
                                                                         test_server, create_global_sns,
                                                                         create_service_sqs):

        with pytest.raises(EnvironmentError, match='Unable to find subscription for xavi') as exc_info:
            await test_server(insanic_application)

        assert exc_info
        assert isinstance(exc_info.value, EnvironmentError)














