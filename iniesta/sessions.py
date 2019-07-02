import aiobotocore
from insanic.conf import settings



class AWSCredentials(object):
    def __init__(self, type):
        self.value = None
        self.type = type

    def __get__(self, instance, owner):
        if self.value is None:
            self.value = getattr(settings, f'INIESTA_{self.type}', None) or getattr(settings, self.type, None)
        return self.value


class BotoSession:
    session = None

    @classmethod
    def get_session(cls, loop=None):
        if cls.session is None:
            cls.session = aiobotocore.get_session(loop=loop)
        return cls.session

    # @classmethod
    # def create_client(cls, resource, *, endpoint_url=None,  **kwargs):
    #
    #
    #
    #     return cls.session.create_client(resource, )

    aws_access_key_id = AWSCredentials('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = AWSCredentials('AWS_SECRET_ACCESS_KEY')
    aws_sqs_region_name = AWSCredentials('bo')

    @classmethod
    def reset_aws_credentials(cls):
        cls.aws_access_key_id = AWSCredentials('AWS_ACCESS_KEY_ID')
        cls.aws_secret_access_key = AWSCredentials('AWS_SECRET_ACCESS_KEY')
