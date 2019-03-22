from . import config
from .sns import SNSClient
from .sqs import SQSClient

from insanic.log import error_logger

class Iniesta:

    @classmethod
    def load_config(cls, settings_object):
        #
        # for c in dir(config):
        #     if c.isupper():
        #         conf = getattr(config, c)
        #         if c == "INIESTA_CACHE":
        #             app.config.INSANIC_CACHES.update(conf)
        #         elif not hasattr(app.config, c):
        #             setattr(app.config, c, conf)
        #
        #
        for c in dir(config):
            if c.isupper():
                conf = getattr(config, c)
                if c == "INIESTA_CACHE":
                    settings_object.INSANIC_CACHES.update(conf)
                elif not hasattr(settings_object, c):
                    setattr(settings_object, c, conf)

    @classmethod
    def attach_listeners(cls, app, *, sns_endpoint_url=None, sqs_endpoint_url=None):

        @app.listener('after_server_start')
        async def after_server_start_poll_sqs_for_messages(app, loop=None, **kwargs):

            environment = app.config.MMT_ENV
            service_name = app.config.SERVICE_NAME

            if app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN is None:
                error_logger.critical("[INIESTA] INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN is not set!")
                raise EnvironmentError("INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN not set in settings!")

            app.xavi = await SNSClient.initialize(
                topic_arn=app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN,
                endpoint_url=sns_endpoint_url
            )

            app.messi = await SQSClient.initialize(
                queue_name=app.config.INIESTA_SQS_QUEUE_NAME_TEMPLATE.format(
                    env=environment, service_name=service_name
                ),
                endpoint_url=sqs_endpoint_url
            )

            await app.messi.confirm_subscription(app.xavi)
            await app.messi.confirm_permission(app.xavi)

            app.messi.start_receiving_messages()

        @app.listener('before_server_stop')
        async def before_server_stop_stop_polling(app, loop=None, **kwargs):
            await app.messi.stop_receiving_messages()

    @classmethod
    def init_app(cls, app, *, sns_endpoint_url=None, sqs_endpoint_url=None):

        cls.load_config(app.config)
        # cls.initialize_clients(app)
        cls.attach_listeners(app,
                             sns_endpoint_url=sns_endpoint_url,
                             sqs_endpoint_url=sqs_endpoint_url)
