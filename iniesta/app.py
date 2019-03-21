from . import config


class Iniesta:

    @classmethod
    def load_config(cls, app):

        for c in dir(config):
            if c.isupper():
                conf = getattr(config, c)
                if c == "INIESTA_CACHE":
                    app.config.INSANIC_CACHES.update(conf)
                elif not hasattr(app.config, c):
                    setattr(app.config, c, conf)

    @classmethod
    def attach_listeners(cls, app):

        return


    @classmethod
    def init_app(cls, app):

        cls.load_config(app)
        cls.attach_listeners(app)
        # patch()
