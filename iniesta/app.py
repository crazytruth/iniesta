from types import MappingProxyType

from insanic import Insanic
from insanic.exceptions import ImproperlyConfigured
from insanic.functional import empty
from sanic.config import Config

from . import config
from .choices import InitializationTypes
from .listeners import IniestaListener
from .utils import filter_list_to_filter_policies


class _Iniesta(object):
    """
    Initializes Iniesta with different methods.
    You should probably not use this. You should
    import just Iniesta.

    :code:`from iniesta import Iniesta`
    """

    def __init__(self) -> None:

        self.config_imported = False
        self._initialization_type = empty

        self.INITIALIZATION_MAPPING = MappingProxyType(
            {
                InitializationTypes.QUEUE_POLLING: self._init_queue_polling,
                InitializationTypes.EVENT_POLLING: self._init_event_polling,
                InitializationTypes.SNS_PRODUCER: self._init_producer,
                InitializationTypes.CUSTOM: self._init_custom,
            }
        )

    @property
    def initialization_type(self) -> InitializationTypes:
        final = InitializationTypes(0)
        if self._initialization_type is empty:
            return final

        for it in self._initialization_type:
            final |= it
        return final

    @initialization_type.setter
    def initialization_type(self, value: InitializationTypes) -> None:
        if not isinstance(value, InitializationTypes):
            raise ValueError("Must be an InitializationTypes choice.")

        if self._initialization_type is empty:
            self._initialization_type = []
        self._initialization_type.append(value)

    def check_global_arn(self, settings_object: Config) -> None:
        if settings_object.INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN is None:
            raise ImproperlyConfigured(
                "INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN not set in settings!"
            )

    def load_config(self, settings_object: Config) -> None:
        if not self.config_imported:
            for c in dir(config):
                if c.isupper():
                    conf = getattr(config, c)
                    if c == "INIESTA_CACHES":
                        settings_object.INSANIC_CACHES.update(conf)
                    elif not hasattr(settings_object, c):
                        setattr(settings_object, c, conf)

            self.config_imported = True

    def unload_config(self, settings_object: Config) -> None:
        for c in dir(config):
            if c.isupper():
                try:
                    delattr(settings_object, c)
                except AttributeError:
                    pass
        self.config_imported = False

    def _order_initialization_type(self, settings_object: Config) -> list:
        try:
            init_types = settings_object.INIESTA_INITIALIZATION_TYPE
            return sorted([InitializationTypes[it] for it in init_types])
        except (KeyError, TypeError):
            raise ImproperlyConfigured(
                f"{str(init_types)} is "
                f"an invalid initialization type. "
                f"Choices are {', '.join(str(i) for i in self.INITIALIZATION_MAPPING.keys())}"
            )

    def _validate_initialization_type(self, settings_object: Config):
        if settings_object.INIESTA_INITIALIZATION_TYPE is None:
            raise ImproperlyConfigured(
                "Please configure INIESTA_INITIALIZATION_TYPE in your config!"
            )

        if not isinstance(
            settings_object.INIESTA_INITIALIZATION_TYPE, (list, tuple)
        ):
            raise ImproperlyConfigured(
                "INIESTA_INITIALIZATION_TYPE type is invalid. Must be list or tuple!"
            )

    def init_app(self, app: Insanic) -> None:
        """
        Initializes the application depending on INIESTA_INITIALIZATION_TYPE set in settings
        """
        if self._initialization_type is not empty:
            raise ImproperlyConfigured("Iniesta has already been initialized!")

        self.load_config(app.config)

        self._validate_initialization_type(app.config)

        initialization_types = self._order_initialization_type(app.config)

        for choice in initialization_types:
            initialization_method = self.INITIALIZATION_MAPPING[choice]
            initialization_method(app)
            self.initialization_type = choice

    def _init_custom(self, app: Insanic) -> None:
        """
        Initializes the application for custom use.

        Actions this takes:

            - Loads iniesta configs
        """
        self.load_config(app.config)

    def _init_producer(self, app: Insanic) -> None:
        """
        Initializes the application with only SNS producing capabilities.
        Checks if the global sns arn exists. If not fails running of application.

        Actions:

            - Checks if global arn is valid
            - Loads iniesta configs

        """
        self.load_config(app.config)

        if not app.config.INIESTA_DRY_RUN:
            # check if global arn exists
            self.check_global_arn(app.config)

            listener = IniestaListener()
            app.register_listener(
                listener.after_server_start_producer_check, "after_server_start"
            )

    def _init_queue_polling(self, app: Insanic) -> None:
        """
        Basic sqs queue polling without the need for checking subscriptions.

        Actions:

            - Loads iniesta configs
            - Attaches listeners to check if queue exists

        """

        self.load_config(app.config)
        if not app.config.INIESTA_DRY_RUN:
            listener = IniestaListener()
            app.register_listener(
                listener.after_server_start_start_queue_polling,
                "after_server_start",
            )
            app.register_listener(
                listener.before_server_stop_stop_polling, "before_server_stop"
            )

    def _init_event_polling(self, app: Insanic) -> None:
        """
        Initializes for event polling.

        Actions:

            - Checks if global arn exists
            - Checks if filters are 0 to avoid receiving all messages
            - Loads iniesta configs
            - Attaches listeners
            - Checks if queue exists (initialize)
            - Checks subscriptions
            - Checks permissions

        """

        self.load_config(app.config)
        if not app.config.INIESTA_DRY_RUN:
            # check if global arn exists
            self.check_global_arn(app.config)

            # check if filters are 0
            if len(app.config.INIESTA_SQS_CONSUMER_FILTERS) == 0:
                raise ImproperlyConfigured(
                    "INIESTA_SQS_CONSUMER_FILTERS is an empty list. "
                    "Please specify events to receive!"
                )

            listener = IniestaListener()

            app.register_listener(
                listener.after_server_start_event_polling, "after_server_start"
            )
            app.register_listener(
                listener.before_server_stop_stop_polling, "before_server_stop"
            )

    def filter_policies(self) -> dict:
        """
        Serializes the defined filter policies that AWS apis can use.
        """
        from insanic.conf import settings

        return filter_list_to_filter_policies(
            settings.INIESTA_SNS_EVENT_KEY,
            settings.INIESTA_SQS_CONSUMER_FILTERS,
        )


Iniesta = _Iniesta()
