import logging
import os
import pwd
import signal
from typing import Dict, Any

import time
from confluent_kafka import SerializingProducer
from confluent_kafka.cimpl import Message
from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.eventsource.cached_table import CachedTable, log_exception
from jlab_jaws.eventsource.listener import EventSourceListener
from jlab_jaws.eventsource.table import TimeoutException

logger = logging.getLogger(__name__)


class MonitorListener(EventSourceListener):

    def on_highwater_timeout(self) -> None:
        pass

    def on_batch(self, msgs: Dict[Any, Message]) -> None:
        for msg in msgs.values():
            print("{}={}".format(msg.key(), msg.value()))

    def on_highwater(self) -> None:
        pass


class ShellTable:

    def __init__(self, etable: CachedTable, params):
        self._etable = etable

        set_log_level_from_env()

        signal.signal(signal.SIGINT, self.__signal_handler)

        try:
            if params.monitor:
                etable.add_listener(MonitorListener())
                etable.start(log_exception)
            else:
                etable.start(log_exception)
                msgs: Dict[Any, Message] = etable.await_get(5)
                self.initial_msgs(msgs, params)
                etable.stop()

        except TimeoutException:
            print("Took too long to obtain list")

    def __signal_handler(self, sig, frame):
        print('Stopping from Ctrl+C!')
        self._etable.stop()

    @staticmethod
    def initial_msgs(msgs: Dict[Any, Message], params):
        if params.export:
            params.export_msgs(msgs)
        else:
            params.disp_table(msgs)


class JAWSProducer:
    """
        This class produces messages with the JAWS expected header.

        Sensible defaults are used to determine BOOTSTRAP_SERVERS (look in env)
        and to handle errors (log them).
    """
    def __init__(self, topic, producer_name, key_serializer, value_serializer):
        set_log_level_from_env()

        self._topic = topic
        self._producer_name = producer_name

        bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
        producer_conf = {'bootstrap.servers': bootstrap_servers,
                         'key.serializer': key_serializer,
                         'value.serializer': value_serializer}

        self._producer = SerializingProducer(producer_conf)
        self._headers = self.__get_headers()

    def send(self, key, value):
        logger.debug("{}={}".format(key, value))
        self._producer.produce(topic=self._topic, headers=self._headers, key=key, value=value,
                               on_delivery=self.__on_delivery)
        self._producer.flush()

    def import_records(self, file, line_to_kv):
        logger.debug("Loading file", file)
        handle = open(file, 'r')
        lines = handle.readlines()

        for line in lines:
            key, value = line_to_kv(line)

            logger.debug("{}={}".format(key, value))
            self._producer.produce(topic=self._topic, headers=self._headers, key=key, value=value,
                                   on_delivery=self.__on_delivery)

        self._producer.flush()

    def __get_headers(self):
        return [('user', pwd.getpwuid(os.getuid()).pw_name),
                ('producer', self._producer_name),
                ('host', os.uname().nodename)]

    @staticmethod
    def __on_delivery(err, msg):
        if err is not None:
            logger.error('Failed: {}'.format(err))
        else:
            logger.debug('Delivered')


def set_log_level_from_env():
    level = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(threadName)-16s %(name)s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S')


def get_registry_client():
    sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    return SchemaRegistryClient(sr_conf)


def get_row_header(headers, timestamp):
    ts = time.ctime(timestamp[1] / 1000)

    user = ''
    producer = ''
    host = ''

    if headers is not None:
        lookup = dict(headers)
        bytez = lookup.get('user', b'')
        user = bytez.decode()
        bytez = lookup.get('producer', b'')
        producer = bytez.decode()
        bytez = lookup.get('host', b'')
        host = bytez.decode()

    return [ts, user, host, producer]
