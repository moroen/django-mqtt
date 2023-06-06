import paho.mqtt.client as mqtt_lib
from random import randint
import logging

from paho.mqtt.client import MQTTMessageInfo
from paho.mqtt.properties import Properties as Properties

from .signals import connected

# from django.dispatch import receiver
# from transport.mqtt.handlers import (
#    on_fail,
#    on_message,
#    on_set_message,
#    on_device_message,
# )

client: mqtt_lib.Client = None
client_id = None
host: str = None
port: int = None
do_restart = False

log = logging.getLogger("mqtt")


class MQTTClient(mqtt_lib.Client):
    host: str = None
    port: int = None
    id: str = None

    topic_queue = []
    connect_handlers = []

    def __init__(
        self,
        client_id: str | None = "",
        clean_session: bool | None = None,
        userdata=None,
        protocol: int = 4,
        transport: str = "tcp",
        reconnect_on_failure: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.id = (
            client_id if client_id is not None else f"python-mqtt-{randint(0, 1000)}"
        )

        log.debug("Init")

        super().__init__(
            client_id,
            clean_session,
            userdata,
            protocol,
            transport,
            reconnect_on_failure,
        )

    def connect(self, host, port=None):
        log.debug("Connecting")

        self.host = host
        self.port = port if port is not None else 1883

        super().loop_start()
        try:
            super().connect(self.host, self.port)
        except ConnectionRefusedError:
            log.error(
                "Connection refused for connection {}:{}".format(self.host, self.port)
            )

    def register_on_connect(self, func):
        log.debug("Adding on_connect handler {}".format(func))
        self.connect_handlers.append(func)

    def on_connect(self, client: mqtt_lib.Client, userdata, flags, rc):
        log.info("Connected to {}:{}".format(self.host, self.port))
        self.process_queues()
        for func in self.connect_handlers:
            func(client, userdata, flags, rc)
        connected.send(self)

    def on_fail(self, client, userdata, flags, rc):
        log.error("Connection failed")

    def on_disconnect(self, client: mqtt_lib.Client, userdata, rc):
        log.debug("Disconnected")

    def publish(
        self,
        topic: str,
        payload: str,
        qos: int = 0,
        retain: bool = False,
        properties: Properties | None = None,
    ) -> MQTTMessageInfo:
        log.debug(
            "Publishing {} on topic {} with retain: {}".format(payload, topic, retain)
        )

        return super().publish(topic, payload, qos, retain, properties)

    # def send(self, topic, payload, retain=False):
    #    log.debug(
    #        "Sending {} on topic {} with retain: {}".format(topic, payload, retain)
    #    )

    def topic(self, topics):
        if not isinstance(topics, list):
            topics = [topics]

        def wrapper(func):
            for topic in topics:
                log.debug(
                    "Adding topic {} with handler {} to queue".format(topic, func)
                )
                self.topic_queue.append((topic, func))
            #    self.subscribe(topic, 1)
            #     self.message_callback_add(topic, func)

            if self.is_connected():
                self.process_queues()

            return func

        return wrapper

    def process_queues(self):
        log.debug("Processing topics queue")
        for topic, func in self.topic_queue:
            log.debug("Subscribing to topic {} with handler {}".format(topic, func))
            self.subscribe(topic)
            self.message_callback_add(topic, func)

        self.topic_queue = []


_instance = MQTTClient()

connect = _instance.connect
disconnect = _instance.disconnect
publish = _instance.publish
topic = _instance.topic


def reconnect(host, port):
    global _instance

    _instance.disconnect()
    _instance.connect(host, port)


def on_connect():
    def wrapper(func):
        _instance.register_on_connect(func)
        return func

    return wrapper


class SendIsDeprecated(Exception):
    pass


def send(*args, **kwargs):
    raise SendIsDeprecated


# def on_connect(client: mqtt_lib.Client, userdata, flags, rc):
#     from .handlers import send_device_configs

#     topics = [
#         # ("{}/+/set".format(config.MQTT_TOPIC), on_set_message),
#         ("{}/+/+/set".format(config.MQTT_TOPIC), on_set_message),
#         ("{}/device/#".format(config.MQTT_TOPIC), on_device_message),
#     ]

#     log.info("Connected to {}:{}".format(host, port))

#     for topic, handler in topics:
#         log.debug("Subscribing to {}".format(topic))
#         client.subscribe(topic, 1)
#         client.message_callback_add(topic, handler)

#     send_device_configs()


# def on_disconnect(client: mqtt_lib.Client, userdata, rc):
#     global do_restart
#     log.info("Disconnected")
#     if do_restart:
#         do_restart = False
#         connect()


# def restart() -> None:
#     global do_restart

#     if client is not None:
#         if client.is_connected() and config.MQTT_ENABLE:
#             do_restart = True
#             client.disconnect()
#         elif not client.is_connected() and config.MQTT_ENABLE:
#             client.connect()
#     else:
#         if config.MQTT_ENABLE:
#             connect()


# def send(topic: str, payload: str, retain=False, qos=0) -> bool:
#     global log
#     log.debug("Sending {} on topic {} with retain: {}".format(payload, topic, retain))

#     if client is None:
#         log.error("Unable to publish, not connected")
#         return False

#     client.publish(topic, payload, retain=retain, qos=qos)
#     return True
