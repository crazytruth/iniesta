import botocore
import pytest

from insanic import Insanic
from insanic.conf import settings
from insanic.exceptions import ImproperlyConfigured

from iniesta import Iniesta
from iniesta.choices import InitializationTypes
from iniesta.listeners import IniestaListener

from .conftest import ALL_INITIALIZATION_TYPES
from .infra import SNSInfra

init_methods_for_producer = [
    "init_producer",
    "prepare_for_delivering_through_pass",
]
init_methods_for_queue_polling = [
    "init_queue_polling",
    "prepare_for_receiving_short_pass",
]
init_methods_for_event_polling = [
    "init_event_polling",
    "prepare_for_receiving_through_pass",
]
init_methods_for_producing_and_consuming = [
    "init_app",
    "prepare_for_passing_and_receiving",
]

init_methods = (
    init_methods_for_producer
    + init_methods_for_queue_polling
    + init_methods_for_event_polling
    + init_methods_for_producing_and_consuming
)


class InitializeFixtures:
    # @pytest.fixture
    # def insanic_application(self):
    #     app = Insanic('xavi')
    #     Iniesta.init_app(app)
    #     yield app

    @pytest.fixture
    def insanic_server(
        self, loop, insanic_application, test_server, monkeypatch
    ):
        return loop.run_until_complete(test_server(insanic_application))


class TestIniestaInitialize(InitializeFixtures):
    @pytest.fixture(autouse=True)
    def set_filters(self, monkeypatch):
        monkeypatch.setattr(
            settings, "INIESTA_SQS_CONSUMER_FILTERS", ["Event"], raising=False
        )

    @pytest.fixture()
    def set_sns_arn(self, monkeypatch):
        monkeypatch.setattr(
            settings, "INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN", "", raising=False
        )

    def _get_function_list(self, listeners):
        functions = []
        for f in listeners:
            if hasattr(f, "__func__"):
                functions.append(f.__func__)
            else:
                functions.append(f)
        return functions

    @pytest.mark.parametrize("initialization_types", ALL_INITIALIZATION_TYPES)
    async def test_init_app(
        self,
        monkeypatch,
        insanic_application,
        set_sns_arn,
        initialization_types,
    ):
        monkeypatch.setattr(
            settings,
            "INIESTA_INITIALIZATION_TYPE",
            initialization_types,
            raising=False,
        )

        Iniesta.init_app(insanic_application)
        final = 0
        for i in initialization_types:
            final |= InitializationTypes[i]

        assert Iniesta.initialization_type == final
        assert Iniesta.config_imported is True

        checks = []

        after_server_start_listener_functions = self._get_function_list(
            insanic_application.listeners["after_server_start"]
        )

        before_server_stop_listener_functions = self._get_function_list(
            insanic_application.listeners["before_server_stop"]
        )

        if InitializationTypes.SNS_PRODUCER.name in initialization_types:

            assert (
                IniestaListener.after_server_start_producer_check
                in after_server_start_listener_functions
            )

            checks.append(InitializationTypes.SNS_PRODUCER.name)

        if InitializationTypes.QUEUE_POLLING.name in initialization_types:

            assert (
                IniestaListener.after_server_start_start_queue_polling
                in after_server_start_listener_functions
            )
            assert (
                IniestaListener.before_server_stop_stop_polling
                in before_server_stop_listener_functions
            )

            checks.append(InitializationTypes.QUEUE_POLLING.name)

        if InitializationTypes.EVENT_POLLING.name in initialization_types:

            assert (
                IniestaListener.after_server_start_event_polling
                in after_server_start_listener_functions
            )
            assert (
                IniestaListener.before_server_stop_stop_polling
                in before_server_stop_listener_functions
            )

            checks.append(InitializationTypes.EVENT_POLLING.name)

        if InitializationTypes.CUSTOM.name in initialization_types:
            checks.append(InitializationTypes.CUSTOM.name)

        assert sorted(checks) == sorted(initialization_types)

    @pytest.mark.parametrize(
        "invalid_initialization_types",
        (
            "",
            "asdad",
            1213,
            None,
            {"a": "b"},
            {"QUEUE_POLLING": "asd"},
            {"asdad": "QUEUE_POLLING"},
            ["asd"],
            ["QUEUE_POLLING", "BAD"],
        ),
    )
    def test_init_app_invalid_choice(
        self,
        monkeypatch,
        insanic_application,
        invalid_initialization_types,
        set_sns_arn,
    ):

        monkeypatch.setattr(
            settings,
            "INIESTA_INITIALIZATION_TYPE",
            invalid_initialization_types,
            raising=False,
        )

        with pytest.raises(ImproperlyConfigured):
            Iniesta.init_app(insanic_application)

    @pytest.mark.parametrize("initialization_types", ALL_INITIALIZATION_TYPES)
    def test_trying_to_initialize_more_than_once(
        self,
        insanic_application,
        set_sns_arn,
        initialization_types,
        monkeypatch,
    ):
        monkeypatch.setattr(
            settings,
            "INIESTA_INITIALIZATION_TYPE",
            initialization_types,
            raising=False,
        )

        Iniesta.init_app(insanic_application)

        if initialization_types != ():
            with pytest.raises(
                ImproperlyConfigured,
                match="Iniesta has already been initialized!",
            ):
                Iniesta.init_app(insanic_application)
        else:
            assert Iniesta.initialization_type == 0
            Iniesta.init_app(insanic_application)

    async def test_insanic_run_sns_not_set(
        self, insanic_application, test_server, monkeypatch
    ):
        monkeypatch.setattr(
            settings,
            "INIESTA_INITIALIZATION_TYPE",
            ["EVENT_POLLING", "SNS_PRODUCER"],
            raising=False,
        )

        with pytest.raises(ImproperlyConfigured) as exc_info:
            Iniesta.init_app(insanic_application)
            await test_server(insanic_application)

        assert "INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN" in str(exc_info.value)

    @pytest.mark.parametrize(
        "topic_arn",
        (
            "something wrong",
            "a:b:c:d:e:f",
            "arn:b:c:d:e:f",
            "arn:aws:sns:ap-northeast-1:e:f",
        ),
    )
    @pytest.mark.parametrize(
        "init_method_name",
        init_methods_for_producer + init_methods_for_event_polling,
    )
    async def test_insanic_run_bad_topic_arn(
        self,
        insanic_application,
        test_server,
        topic_arn,
        init_method_name,
        monkeypatch,
    ):
        monkeypatch.setattr(
            settings,
            "INIESTA_INITIALIZATION_TYPE",
            ["EVENT_POLLING", "SNS_PRODUCER"],
            raising=False,
        )

        monkeypatch.setattr(
            settings, "INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN", topic_arn
        )

        Iniesta.init_app(insanic_application)
        with pytest.raises(botocore.exceptions.ClientError) as exc_info:
            await test_server(insanic_application)

        assert exc_info


class TestInitializeWithSNS(SNSInfra):
    queue_name = "iniesta-tests-xavi"

    @pytest.fixture(autouse=True)
    def set_filters(self, monkeypatch):
        monkeypatch.setattr(
            settings, "INIESTA_SQS_CONSUMER_FILTERS", ["Event"], raising=False
        )

    @pytest.fixture()
    def insanic_application(
        self, set_global_topic_arn, set_filters, monkeypatch,
    ):
        monkeypatch.setattr(
            settings,
            "INIESTA_INITIALIZATION_TYPE",
            ["EVENT_POLLING", "SNS_PRODUCER"],
            raising=False,
        )

        app = Insanic("xavi")
        Iniesta.init_app(app)
        yield app

    @pytest.fixture(autouse=True)
    def set_global_topic_arn(self, create_global_sns, monkeypatch):
        monkeypatch.setattr(
            settings,
            "INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN",
            create_global_sns["TopicArn"],
            raising=False,
        )

    async def test_insanic_run_with_topic_but_no_queue(
        self, insanic_application, test_server, create_global_sns
    ):
        with pytest.raises(botocore.exceptions.ClientError) as exc_info:
            await test_server(insanic_application)

        assert exc_info
        assert exc_info.typename == "QueueDoesNotExist"

    async def test_insanic_run_with_topic_and_queue_but_no_subscriptions(
        self,
        insanic_application,
        test_server,
        create_global_sns,
        create_service_sqs,
    ):
        with pytest.raises(
            EnvironmentError, match="Unable to find subscription for xavi"
        ) as exc_info:
            await test_server(insanic_application)

        assert exc_info
        assert isinstance(exc_info.value, EnvironmentError)
