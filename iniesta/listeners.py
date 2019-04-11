from iniesta.sns import SNSClient
from iniesta.sqs import SQSClient


class IniestaListener:

    async def _initialize_sns(self, app):
        app.xavi = await SNSClient.initialize(
            topic_arn=app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN
        )

    async def _initialize_sqs(self, app):

        app.messi = await SQSClient.initialize(
            queue_name=app.config.INIESTA_SQS_QUEUE_NAME_TEMPLATE.format(
                env=app.config.MMT_ENV,
                service_name=app.config.SERVICE_NAME
            )
        )

    def _start_polling(self, app):
        app.messi.start_receiving_messages()

    async def _stop_polling(self, app):
        await app.messi.stop_receiving_messages()

    # actual listeners
    async def after_server_start_producer_check(self, app, loop=None, **kwargs):
        await self._initialize_sns(app)

    async def after_server_start_start_queue_polling(self, app, loop=None, **kwargs):
        await self._initialize_sqs(app)
        self._start_polling(app)

    async def after_server_start_event_polling(self, app, loop=None, **kwargs):
        """
        start event polling listener. checks if all necessary components
        have been initialized

        :param app:
        :param loop:
        :param kwargs:
        :return:
        """
        await self._initialize_sqs(app)

        await app.messi.confirm_subscription(
            app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN,

        )
        await app.messi.confirm_permission()

        self._start_polling(app)

    async def before_server_stop_stop_polling(self, app, loop=None, **kwargs):
        """
        needs to be attached when start_polling gets attached

        :param app:
        :param loop:
        :param kwargs:
        :return:
        """
        await self._stop_polling(app)
