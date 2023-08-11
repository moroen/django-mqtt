from django.apps import AppConfig
from django.dispatch import receiver
from django.conf import settings
from .core import connect, disconnect, reconnect
import logging
from os import environ
from time import sleep

log = logging.getLogger("mqtt")


class DjangoMqttConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_mqtt"

    def ready(self) -> None:
        if not (environ.get("RUN_MAIN")):
            return

        config = getattr(settings, "MQTT_CONFIG", None)
        if config is None:
            log.debug("No settings specified")
        else:
            use_constance = (
                config["USE_CONSTANCE"] if "USE_CONSTANCE" in config else False
            )
            if use_constance:
                log.debug("Using constance")
                from constance import config
                from constance.signals import config_updated

                @receiver(config_updated)
                def constance_updated(sender, key, old_value, new_value, **kwargs):
                    if old_value is None:
                        return

                    host = new_value if key == "MQTT_HOST" else config.MQTT_HOST
                    port = new_value if key == "MQTT_PORT" else config.MQTT_PORT

                    log.debug(
                        "Constance settings changed, reconnecting to {}:{}".format(
                            host, port
                        )
                    )

                    if key == "MQTT_ENABLE":
                        if new_value:
                            reconnect(host=host, port=port)
                        else:
                            disconnect()
                        return

                    reconnect(host=host, port=port)

                if config.MQTT_ENABLE:
                    connect(host=config.MQTT_HOST, port=config.MQTT_PORT)
                else:
                    log.debug("Disabled by settings")
            else:
                if "HOST" in config:
                    host = config["HOST"]
                else:
                    host = "127.0.0.1"
                    log.warn(
                        "Using settings from settings.py, but no HOST specified. Using default (127.0.0.1)"
                    )

                if "PORT" in config:
                    port = config["PORT"]
                else:
                    port = 1883
                    log.warn(
                        "Using settings from settings.py, but no PORT specified. Using default (1883)"
                    )

                connect(host=host, port=port)

        return super().ready()
