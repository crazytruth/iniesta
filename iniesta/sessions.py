import aiobotocore


class BotoSession:
    session = None

    @classmethod
    def get_session(cls, loop=None):
        if cls.session is None:
            cls.session = aiobotocore.get_session(loop=loop)
        return cls.session