from functools import partial

from insanic.log import error_logger, logger

from . import config
from .listeners import after_server_start_verify_sns, \
    after_server_start_verify_sqs, before_server_stop_stop_polling
from .sns import SNSClient
from .sqs import SQSClient


class Iniesta:

    @classmethod
    def load_config(cls, settings_object):

        for c in dir(config):
            if c.isupper():
                conf = getattr(config, c)
                if c == "INIESTA_CACHE":
                    settings_object.INSANIC_CACHES.update(conf)
                elif not hasattr(settings_object, c):
                    setattr(settings_object, c, conf)

    @classmethod
    def check_prerequisites(cls, app):
        if app.config.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN is None:
            error_logger.critical("[INIESTA] INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN is not set!")
            raise EnvironmentError("INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN not set in settings!")

    @classmethod
    def attach_listeners_for_producer(cls, app, *, sns_endpoint_url=None):

        after_server_start_event = partial(after_server_start_verify_sns, sns_endpoint_url=sns_endpoint_url)

        app.register_listener(after_server_start_event, 'after_server_start')

    @classmethod
    def attach_listeners_for_consumers(cls, app, *, sqs_endpoint_url=None,
                                       sns_endpoint_url=None):

        if len(app.config.INIESTA_SQS_CONSUMER_FILTERS) == 0:
            logger.debug('[INIESTA] Skipping attaching because no filters are defined.')
            return

        after_server_start_event = partial(after_server_start_verify_sqs,
                                           sns_endpoint_url=sns_endpoint_url,
                                           sqs_endpoint_url=sqs_endpoint_url)

        app.register_listener(after_server_start_event, 'after_server_start')
        app.register_listener(before_server_stop_stop_polling, 'before_server_stop')

    # @classmethod
    # def init_app(cls, app, *, sns_endpoint_url=None, sqs_endpoint_url=None):
    #     """
    #     for initializing app
    #
    #     :param app: insanic application instaance
    #     :param sns_endpoint_url: mainly used for testing
    #     :param sqs_endpoint_url: mainly used for testing
    #     :return:
    #     """
    #     cls.check_prerequisites(app)
    #     cls.load_config(app.config)
    #     cls.attach_listeners_for_producer(app,
    #                                       sns_endpoint_url=sns_endpoint_url)
    #     cls.attach_listeners_for_consumers(app,
    #                                        sqs_endpoint_url=sqs_endpoint_url)

    @classmethod
    def init_producer(cls, app, *, sns_endpoint_url=None):
        cls.check_prerequisites(app)
        cls.load_config(app.config)
        cls.attach_listeners_for_producer(app, sns_endpoint_url=sns_endpoint_url)

    @classmethod
    def init_queue_polling(cls, app, *, sqs_endpoint_url=None):
        """
        Basic sqs queue polling without the need for checking subscriptions
        dont need to check prerequisites?
        load configs
        attach listeners to check if queue exists

        :param app:
        :param sqs_endpoint_url:
        :return:
        """

        cls.load_config(app.config)
        cls.attach_listeners_for_consumers(app, sqs_endpoint_url=sqs_endpoint_url)

    @classmethod
    def init_event_polling(cls, app, *, sqs_endpoint_url=None):


        # check prerequistives?
        # need to check if filters are 0 to avoid receiving all messages
        # load configs
        # check if queue exists
        # check subscriptions
        # check permissions
        cls.check_prerequisites(app)

        cls.init_consumer(app, sqs_endpoint_url=sqs_endpoint_url)


