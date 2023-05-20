from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from os import environ


class MqttConfig(AppConfig):
    name = "django_mqtt"
    verbose_name = _("DJANGO-MQTT")
    # default_auto_field = "django.db.models.AutoField"

    def ready(self):
        if environ.get("DJANGO_MQTT_STARTED") == "true":
            # Avoid staring app twice when using the development server
            return

        from . import core

        environ["DJANGO_MQTT_STARTED"] = "true"
        core.connect(host="127.0.0.1", port=1883)
