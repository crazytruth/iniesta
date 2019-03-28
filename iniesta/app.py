from . import config
from .choices import InitializationTypes
from .exceptions import ImproperlyConfigured
from .listeners import IniestaListener


class _Initializer(type):

    def __getattribute__(cls, item):
        if item.startswith('init_'):
            if cls.initialization_type is not None:
                raise ImproperlyConfigured('Iniesta has already been initialized!')
        return super().__getattribute__(item)


class Iniesta(metaclass=_Initializer):

    config_imported = False
    _initialization_type = None

    @property
    def initialization_type(self):
        return self._initialization_type

    @initialization_type.setter
    def initialization_type(self, value):
        if self._initialization_type is None:
            self.initialization_type = value
        else:
            self.initialization_type = self.initialization_type | value

    @classmethod
    def check_global_arn(cls, settings_object):
        if settings_object.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN is None:
            raise ImproperlyConfigured("INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN not set in settings!")

    @classmethod
    def load_config(cls, settings_object):
        if not cls.config_imported:
            for c in dir(config):
                if c.isupper():
                    conf = getattr(config, c)
                    if c == "INIESTA_CACHE":
                        settings_object.INSANIC_CACHES.update(conf)
                    elif not hasattr(settings_object, c):
                        setattr(settings_object, c, conf)

            cls.config_imported = True

    @classmethod
    def init_app(cls, app):
        cls._init_producer_and_polling(app)

    @classmethod
    def _init_producer_and_polling(cls, app):
        """

        :param app:
        :return:
        """
        cls._init_producer(app)
        cls._init_event_polling(app)

    @classmethod
    def init_producer(cls, app):
        cls._init_producer(app)

    @classmethod
    def _init_producer(cls, app):
        """
        check if global arn is set
        load configs

        :param app:
        :return:
        """
        cls.load_config(app.config)
        # check if global arn exists
        cls.check_global_arn(app.config)

        listener = IniestaListener()
        app.register_listener(listener.after_server_start_producer_check,
                              'after_server_start')
        cls.initialization_type = InitializationTypes.SNS_PRODUCER

    @classmethod
    def init_queue_polling(cls, app):
        cls._init_queue_polling(app)

    @classmethod
    def _init_queue_polling(cls, app):
        """
        Basic sqs queue polling without the need for checking subscriptions
        load configs
        attach listeners to check if queue exists

        :param app:
        :return:
        """
        cls.load_config(app.config)

        listener = IniestaListener()
        app.register_listener(listener.after_server_start_start_queue_polling,
                              'after_server_start')
        app.register_listener(listener.before_server_stop_stop_polling,
                              'before_server_stop')
        cls.initialization_type = InitializationTypes.QUEUE_POLLING

    @classmethod
    def init_event_polling(cls, app):
        cls._init_event_polling(app)

    @classmethod
    def _init_event_polling(cls, app):
        """
        # check if global arn exists
        # need to check if filters are 0 to avoid receiving all messages
        # load configs

        - from listeners
        check if queue exists (initialize)
        check subscriptions
        check permissions

        :param app:
        :return:
        """
        # TODO: need to check order of plugin vs vault
        cls.load_config(app.config)

        # check if global arn exists
        cls.check_global_arn(app.config)

        # check if filters are 0
        if len(app.config.INIESTA_SQS_CONSUMER_FILTERS) == 0:
            raise ImproperlyConfigured("INIESTA_SQS_CONSUMER_FILTERS is an empty list. "
                                       "Please specifiy events to receive!")

        listener = IniestaListener()

        app.register_listener(listener.after_server_start_event_polling,
                              'after_server_start')
        app.register_listener(listener.before_server_stop_stop_polling,
                              'before_server_stop')
        cls.initialization_type = InitializationTypes.EVENT_POLLING

    @classmethod
    def prepare_for_delivering_through_pass(cls, app):
        """
        equivalent of init_producer

        :param app:
        :return:
        """
        cls.init_producer(app)

    @classmethod
    def prepare_for_receiving_short_pass(cls, app):
        cls.init_queue_polling(app)

    @classmethod
    def prepare_for_receiving_through_pass(cls, app):
        cls.init_event_polling(app)

    @classmethod
    def prepare_for_passing_and_receiving(cls, app):
        cls.init_app(app)
