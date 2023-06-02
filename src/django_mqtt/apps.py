from django.apps import AppConfig
from django.dispatch import receiver
from django.conf import settings
from .core import connect, disconnect, reconnect
import logging
from time import sleep

log = logging.getLogger("mqtt")


class DjangoMqttConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_mqtt"

    def ready(self) -> None:
        log.debug("Ready")

        try:
            if settings.MQTT_CONFIG["USE_CONSTANCE"]:
                from constance import config
                from constance.signals import config_updated

                @receiver(config_updated)
                def constance_updated(sender, key, old_value, new_value, **kwargs):
                    if old_value is None:
                        return

                    if key == "MQTT_HOST":
                        reconnect(host=new_value, port=config.MQTT_PORT)

                connect(host=config.MQTT_HOST, port=config.MQTT_PORT)
        except AttributeError:
            log.debug("Use constance not defined")

        return super().ready()
