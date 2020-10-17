import pytest
import uuid

from insanic.conf import settings
from iniesta.sessions import BotoSession


class TestBotoSession:
    @pytest.fixture(autouse=True)
    def reset_session(self):
        yield

        BotoSession.reset_aws_credentials()

    async def test_boto_session_singleton(self):
        session1 = BotoSession.get_session()

        assert session1 is not None

        session2 = BotoSession.get_session()

        assert session1 is session2

    @pytest.mark.parametrize("access_key_id_prefix", ["iniesta", ""])
    @pytest.mark.parametrize("secret_access_key_prefix", ["iniesta", ""])
    def test_aws_credentials_fallback(
        self, monkeypatch, access_key_id_prefix, secret_access_key_prefix
    ):
        access_key_id = uuid.uuid4()
        secret_access_key = uuid.uuid4()

        access_key_id_tokens = ["AWS", "ACCESS", "KEY", "ID"]
        secret_access_key_tokens = ["AWS", "SECRET", "ACCESS", "KEY"]
        monkeypatch.setattr(
            settings,
            "_".join(access_key_id_tokens),
            access_key_id,
            raising=False,
        )
        monkeypatch.setattr(
            settings,
            "_".join(secret_access_key_tokens),
            secret_access_key,
            raising=False,
        )

        if access_key_id_prefix:
            iniesta_access_key_id = uuid.uuid4()

            assert access_key_id != iniesta_access_key_id

            access_key_id_tokens.insert(0, access_key_id_prefix.upper())
            monkeypatch.setattr(
                settings,
                "_".join(access_key_id_tokens),
                iniesta_access_key_id,
                raising=False,
            )

            assert BotoSession.aws_access_key_id == iniesta_access_key_id
        else:
            assert BotoSession.aws_access_key_id == access_key_id

        if secret_access_key_prefix:
            iniesta_secret_access_key = uuid.uuid4()

            assert secret_access_key != iniesta_secret_access_key

            secret_access_key_tokens.insert(0, secret_access_key_prefix.upper())
            monkeypatch.setattr(
                settings,
                "_".join(secret_access_key_tokens),
                iniesta_secret_access_key,
                raising=False,
            )

            assert (
                BotoSession.aws_secret_access_key == iniesta_secret_access_key
            )
        else:
            assert BotoSession.aws_secret_access_key == secret_access_key

        assert BotoSession.aws_access_key_id is not None
        assert BotoSession.aws_secret_access_key is not None
