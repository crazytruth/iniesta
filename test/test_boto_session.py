from iniesta.sessions import BotoSession


class TestBotoSession:

    def test_boto_session_singleton(self):
        session1 = BotoSession.get_session()

        assert session1 is not None

        session2 = BotoSession.get_session()

        assert session1 is session2


