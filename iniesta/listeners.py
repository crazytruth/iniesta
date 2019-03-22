from insanic.log import error_logger

from iniesta.sns import SNSClient
from iniesta.sqs import SQSClient

async def after_server_start_verify_sns(app, loop=None, sns_endpoint_url=None, **kwargs):
    if app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN is None:
        raise EnvironmentError("INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN not set in settings!")

    app.xavi = await SNSClient.initialize(
        topic_arn=app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN,
        endpoint_url=sns_endpoint_url
    )


async def before_server_stop_stop_polling(app, loop=None, **kwargs):
    await app.messi.stop_receiving_messages()


async def after_server_start_verify_sqs_and_start_poll(app, loop=None, sns_endpoint_url=None,
                                        sqs_endpoint_url=None, **kwargs):

    app.messi = await SQSClient.initialize(
        queue_name=app.config.INIESTA_SQS_QUEUE_NAME_TEMPLATE.format(
            env=app.config.MMT_ENV,
            service_name=app.config.SERVICE_NAME
        ),
        endpoint_url=sqs_endpoint_url
    )

    await app.messi.confirm_subscription(
        app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN,
        sns_endpoint_url=sns_endpoint_url
    )
    await app.messi.confirm_permission(
        app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN
    )

    app.messi.start_receiving_messages()