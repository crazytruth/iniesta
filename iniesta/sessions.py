import os

import aiobotocore
from insanic.conf import settings


class AWSCredentials(object):
    def __init__(self, type: str):
        self.value = None
        self.type = type

    def __get__(self, instance, owner) -> str:
        if self.value is None:
            self.value = (
                os.environ.get(self.type, None)
                or getattr(settings, f"INIESTA_{self.type}", None)
                or getattr(settings, self.type, None)
            )
        return self.value


class BotoSession:
    session = None

    @classmethod
    def get_session(cls):
        if cls.session is None:
            cls.session = aiobotocore.get_session()
        return cls.session

    aws_access_key_id = AWSCredentials("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = AWSCredentials("AWS_SECRET_ACCESS_KEY")
    aws_default_region = AWSCredentials("AWS_DEFAULT_REGION")

    @classmethod
    def reset_aws_credentials(cls):
        cls.aws_access_key_id = AWSCredentials("AWS_ACCESS_KEY_ID")
        cls.aws_secret_access_key = AWSCredentials("AWS_SECRET_ACCESS_KEY")
        cls.aws_default_region = AWSCredentials("AWS_DEFAULT_REGION")
