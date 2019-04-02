import botocore
import pytest

from insanic import Insanic
from insanic.conf import settings
from iniesta import Iniesta, config
from iniesta.exceptions import ImproperlyConfigured
from iniesta.listeners import IniestaListener


from .infra import SNSInfra

init_methods_for_producer = ['init_producer',
                             'prepare_for_delivering_through_pass']
init_methods_for_queue_polling = ['init_queue_polling',
                                  'prepare_for_receiving_short_pass']
init_methods_for_event_polling = ['init_event_polling',
                                  'prepare_for_receiving_through_pass']
init_methods_for_producing_and_consuming = ['init_app',
                                            'prepare_for_passing_and_receiving']

init_methods = init_methods_for_producer + \
               init_methods_for_queue_polling + \
               init_methods_for_event_polling + \
               init_methods_for_producing_and_consuming

class InitializeFixtures:
    # @pytest.fixture
    # def insanic_application(self):
    #     app = Insanic('xavi')
    #     Iniesta.init_app(app)
    #     yield app

    @pytest.fixture
    def insanic_server(self, loop, insanic_application, test_server, monkeypatch):
        return loop.run_until_complete(test_server(insanic_application))


class TestIniestaInitialize(InitializeFixtures):
    @pytest.fixture(autouse=True)
    def set_filters(self, monkeypatch):
        monkeypatch.setattr(settings, "INIESTA_SQS_CONSUMER_FILTERS", ["Event"], raising=False)

    @pytest.fixture()
    def set_sns_arn(self, monkeypatch):
        monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN', '', raising=False)


    def _get_function_list(self, listeners):

        l = []

        for f in listeners:
            if hasattr(f, '__func__'):
                l.append(f.__func__)
            else:
                l.append(f)
        return l

    @pytest.mark.parametrize('init_method_name', init_methods_for_producer)
    def test_init_producer(self, insanic_application, init_method_name, set_sns_arn):

        init_method = getattr(Iniesta, init_method_name)
        init_method(insanic_application)

        assert Iniesta.initialization_type is not None
        assert Iniesta.config_imported is True

        listener_functions = self._get_function_list(
            insanic_application.listeners['after_server_start']
        )

        assert IniestaListener.after_server_start_producer_check in listener_functions

    @pytest.mark.parametrize('init_method_name', init_methods_for_queue_polling)
    def test_init_queue_polling(self, insanic_application, init_method_name):

        init_method = getattr(Iniesta, init_method_name)
        init_method(insanic_application)

        assert Iniesta.initialization_type is not None
        assert Iniesta.config_imported is True

        after_server_start_listener_functions = self._get_function_list(
            insanic_application.listeners['after_server_start']
        )

        before_server_stop_listener_functions = self._get_function_list(
            insanic_application.listeners['before_server_stop']
        )

        assert IniestaListener.after_server_start_start_queue_polling in after_server_start_listener_functions
        assert IniestaListener.before_server_stop_stop_polling in before_server_stop_listener_functions

    @pytest.mark.parametrize('init_method_name', init_methods_for_event_polling)
    def test_init_event_polling(self, insanic_application, init_method_name, set_sns_arn):

        init_method = getattr(Iniesta, init_method_name)
        init_method(insanic_application)

        assert Iniesta.initialization_type is not None
        assert Iniesta.config_imported is True

        after_server_start_listener_functions = self._get_function_list(
            insanic_application.listeners['after_server_start']
        )
        before_server_stop_listener_functions = self._get_function_list(
            insanic_application.listeners['before_server_stop']
        )

        assert IniestaListener.after_server_start_event_polling in after_server_start_listener_functions
        assert IniestaListener.before_server_stop_stop_polling in before_server_stop_listener_functions


    @pytest.mark.parametrize('init_method_name', init_methods_for_producing_and_consuming)
    def test_init_passing_and_receiving(self, insanic_application, init_method_name, set_sns_arn):

        init_method = getattr(Iniesta, init_method_name)

        init_method(insanic_application)

        assert Iniesta.initialization_type is not None
        assert Iniesta.config_imported is True

        after_server_start_listener_functions = self._get_function_list(
            insanic_application.listeners['after_server_start']
        )
        before_server_stop_listener_functions = self._get_function_list(
            insanic_application.listeners['before_server_stop']
        )

        assert IniestaListener.after_server_start_producer_check in after_server_start_listener_functions
        assert IniestaListener.after_server_start_event_polling in after_server_start_listener_functions
        assert IniestaListener.before_server_stop_stop_polling in before_server_stop_listener_functions

    @pytest.mark.parametrize('first_init', init_methods)
    @pytest.mark.parametrize('second_init', init_methods)
    def test_trying_to_initialize_more_than_once(self, insanic_application, first_init, second_init, set_sns_arn):

        first_init_method = getattr(Iniesta, first_init)


        first_init_method(insanic_application)

        with pytest.raises(ImproperlyConfigured,
                           match="Iniesta has already been initialized!"):
            second_init_method = getattr(Iniesta, second_init)
            second_init_method(insanic_application)


    @pytest.mark.parametrize('init_method_name', init_methods_for_producer + init_methods_for_event_polling)
    async def test_insanic_run_sns_not_set(self, insanic_application, test_server, init_method_name):

        init_method = getattr(Iniesta, init_method_name)

        with pytest.raises(ImproperlyConfigured) as exc_info:
            init_method(insanic_application)
            await test_server(insanic_application)

        assert 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN' in str(exc_info.value)

    @pytest.mark.parametrize("topic_arn", (
        "something wrong",
        "a:b:c:d:e:f",
        "arn:b:c:d:e:f",
        "arn:aws:sns:ap-northeast-1:e:f",
    ))
    @pytest.mark.parametrize('init_method_name', init_methods_for_producer + init_methods_for_event_polling)
    async def test_insanic_run_bad_topic_arn(self, insanic_application, test_server,
                                             topic_arn, init_method_name, monkeypatch):

        monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN', topic_arn)

        init_method = getattr(Iniesta, init_method_name)
        init_method(insanic_application)
        with pytest.raises(botocore.exceptions.ClientError) as exc_info:
            await test_server(insanic_application)

        assert exc_info


class TestInitializeWithSNS(SNSInfra):
    queue_name = "iniesta-test-xavi"

    @pytest.fixture(autouse=True)
    def set_filters(self, monkeypatch):
        monkeypatch.setattr(settings, "INIESTA_SQS_CONSUMER_FILTERS", ["Event"], raising=False)

    @pytest.fixture()
    def insanic_application(self, sns_endpoint_url, sqs_endpoint_url, set_global_topic_arn, set_filters):

        app = Insanic("xavi")

        Iniesta.init_app(app)
        yield app

    @pytest.fixture(autouse=True)
    def set_global_topic_arn(self, create_global_sns, monkeypatch):
        monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN',
                            create_global_sns['TopicArn'],
                            raising=False)

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














