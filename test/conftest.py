import pytest
import uuid

from insanic import Insanic
from insanic.conf import settings
from iniesta.app import Iniesta
from iniesta.sessions import BotoSession


settings.configure(SERVICE_NAME="iniesta",
                   GATEWAY_REGISTRATION_ENABLED=False,
                   MMT_ENV="test",
                   TRACING_ENABLED=False,
                   GRPC_SERVE=False)


@pytest.fixture(autouse=True)
def initialize_application():
    app = Insanic("iniesta")
    Iniesta.init_app(app)
    yield app



@pytest.fixture(scope="session")
def session_id():
    return uuid.uuid4().hex

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