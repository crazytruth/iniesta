import pytest
import uuid
from itertools import permutations

from insanic import Insanic
from insanic.conf import settings
from insanic.functional import empty
from pytest_redis import factories

from iniesta.app import Iniesta
from iniesta.choices import InitializationTypes
from iniesta.sessions import BotoSession


settings.configure(
    SERVICE_NAME="iniesta",
    ENFORCE_APPLICATION_VERSION=False,
    AWS_ACCESS_KEY_ID="testing",
    AWS_SECRET_ACCESS_KEY="testing",
    AWS_DEFAULT_REGION="us-east-1",
    ENVIRONMENT="tests",
)

for cache_name, cache_config in settings.INSANIC_CACHES.items():
    globals()[f"redisdb_{cache_name}"] = factories.redisdb(
        "redis_nooproc", dbnum=cache_config.get("DATABASE")
    )

redisdb = factories.redisdb("redis_nooproc")


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


@pytest.fixture(scope="function")
def function_id():
    return uuid.uuid4().hex


@pytest.fixture(autouse=True)
def reset_session():
    yield
    BotoSession.reset_aws_credentials()


@pytest.fixture(autouse=True)
def set_redis_connection_info(redisdb, monkeypatch):

    host = redisdb.connection_pool.connection_kwargs["host"]
    port = redisdb.connection_pool.connection_kwargs["port"]

    insanic_caches = settings.INSANIC_CACHES.copy()

    for cache_name in insanic_caches.keys():
        insanic_caches[cache_name]["HOST"] = host
        insanic_caches[cache_name]["PORT"] = int(port)

    caches = settings.CACHES.copy()

    for cache_name in caches.keys():
        caches[cache_name]["HOST"] = "127.0.0.1"
        caches[cache_name]["PORT"] = int(port)

    monkeypatch.setattr(settings, "INSANIC_CACHES", insanic_caches)
    monkeypatch.setattr(settings, "CACHES", caches)


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
ALL_INITIALIZATION_TYPES = sum(
    [
        list(permutations([i.name for i in InitializationTypes], i))
        for i in range(4)
    ],
    [],
)
