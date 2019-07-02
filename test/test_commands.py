import pytest

from insanic.conf import settings
from iniesta import cli
from click.testing import CliRunner

from .infra import SNSInfra



class TestCommands(SNSInfra):

    @pytest.fixture()
    def runner(self):
        yield CliRunner()

    def test_publish_success(self, runner, start_local_aws, create_global_sns, sns_endpoint_url, monkeypatch):
        monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN', create_global_sns['TopicArn'])

        event = 'engineering.division'
        message_body = "help.me"
        result = runner.invoke(cli.publish, ['-e', event, '-m', message_body])

        assert result.exit_code == 0, result.output

        output = result.output.split('\n')

        assert output[0] == 'Publish Success!'
        assert output[1] == "REQUEST INFO"
        assert output[2] == f'Message Event : {event}'
        assert output[3] == f'Message Data : {message_body}'
        assert output[4].startswith('Full Payload : ')
        assert output[5].startswith('Message Length : ')
        assert output[6] == "RESPONSE INFO"
        assert output[7].startswith('Message ID : ')
        assert output[8].startswith('Message Length : ')

    # def test_publish_fail(self, runner, sns_endpoint_url, monkeypatch):
    #     # monkeypatch.setattr(settings, 'INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN', create_global_sns['TopicArn'])
    #
    #     event = 'engineering.division'
    #     message_body = "help.me"
    #     result = runner.invoke(cli.publish, ['-e', event, '-m', message_body])
    #
    #     assert result.exit_code == 0, result.output
    #
    #     output = result.output.split('\n')
    #
    #     assert output[0] == 'Publish Success!'
    #     assert output[1] == "REQUEST INFO"
    #     assert output[2] == f'Message Event : {event}'
    #     assert output[3] == f'Message Data : {message_body}'
    #     assert output[4].startswith('Full Payload : ')
    #     assert output[5].startswith('Message Length : ')
    #     assert output[6] == "RESPONSE INFO"
    #     assert output[7].startswith('Message ID : ')
    #     assert output[8].startswith('Message Length : ')
    #
    #
    #
    #
    #




