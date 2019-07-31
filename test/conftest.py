import pytest
import uuid
from itertools import permutations

from insanic import Insanic
from insanic.conf import settings
from insanic.functional import empty
from iniesta.app import Iniesta
from iniesta.choices import InitializationTypes
from iniesta.sessions import BotoSession


settings.configure(SERVICE_NAME="iniesta",
                   GATEWAY_REGISTRATION_ENABLED=False,
                   MMT_ENV="test",
                   TRACING_ENABLED=False,
                   GRPC_SERVE=False)


@pytest.fixture(autouse=True)
def insanic_application():
    app = Insanic("xavi")

    yield app


@pytest.fixture
def initialize_for_passing(insanic_application):
    Iniesta.init_producer(insanic_application)
    yield insanic_application


@pytest.fixture
def initialize_for_receiving_short_passes(insanic_application):
    Iniesta.init_queue_polling(insanic_application)
    yield insanic_application


@pytest.fixture
def initialize_for_receiving_through_passes(insanic_application):
    Iniesta.init_event_polling(insanic_application)
    yield insanic_application


@pytest.fixture
def initialize_for_passing_and_receiving(insanic_application):
    Iniesta.init_app(insanic_application)
    yield insanic_application


@pytest.fixture(scope="session")
def session_id():
    return uuid.uuid4().hex

@pytest.fixture(scope="module")
def module_id():
    return uuid.uuid4().hex

@pytest.fixture(scope='function')
def function_id():
    return uuid.uuid4().hex


@pytest.fixture(autouse=True)
def reset_session():
    yield
    BotoSession.reset_aws_credentials()

@pytest.fixture(autouse=True)
def set_redis_connection_info(redisdb, monkeypatch):
    port = redisdb.connection_pool.connection_kwargs['path'].split('/')[-1].split('.')[1]
    db = redisdb.connection_pool.connection_kwargs['db']

    monkeypatch.setattr(settings, 'REDIS_PORT', int(port))
    monkeypatch.setattr(settings, 'REDIS_HOST', '127.0.0.1')
    monkeypatch.setattr(settings, 'REDIS_DB', db)


@pytest.fixture(autouse=True)
def reset_boto_session():
    BotoSession.session = None
    yield
    BotoSession.session = None
    BotoSession.reset_aws_credentials()


@pytest.fixture(autouse=True)
def reset_iniesta():
    yield

    Iniesta._initialization_type = empty
    Iniesta.config_imported = False


# do not use this code in production, only for tests!!!
# very inefficient. creates a flat list with lists
ALL_INITIALIZATION_TYPES = sum([list(permutations([i.name for i in InitializationTypes], i)) for i in range(4)], [])