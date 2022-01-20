import json
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
from tabulate import tabulate

logger = logging.getLogger(__name__)


class MonitorListener(EventSourceListener):

    def on_highwater_timeout(self) -> None:
        pass

    def on_batch(self, msgs: Dict[Any, Message]) -> None:
        for msg in msgs.values():
            print("{}={}".format(msg.key(), msg.value()))

    def on_highwater(self) -> None:
        pass


class StringSerde:
    def to_dict(self, value):
        return {"value": value}


class JAWSConsumer(CachedTable):

    def __init__(self, topic, consumer_name, key_deserializer, value_deserializer):
        set_log_level_from_env()

        signal.signal(signal.SIGINT, self.__signal_handler)

        ts = time.time()

        bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
        config = {'topic': topic,
                  'bootstrap.servers': bootstrap_servers,
                  'key.deserializer': key_deserializer,
                  'value.deserializer': value_deserializer,
                  'group.id': consumer_name + str(ts)}

        super().__init__(config)

    def print_records_continuous(self):
        self.add_listener(MonitorListener())
        self.start(log_exception)

    def print_table(self, msg_to_list, head=[], nometa=False, filter_if=lambda key, value: True):
        records = self.get_records()

        table = []

        if not nometa:
            head = ["Timestamp", "User", "Host", "Produced By"] + head

        for record in records.values():
            row = self.__get_row(record, msg_to_list, filter_if, nometa)
            if row is not None:
                table.append(row)

        # Truncate long cells
        table = [[(c if len(str(c)) < 30 else str(c)[:27] + "...") for c in row] for row in table]

        print(tabulate(table, head))

    def export_records(self, value_serde=StringSerde(), filter_if=lambda key, value: True):
        records = self.get_records()

        sortedtable = sorted(records.items())

        for msg in sortedtable:
            key = msg[0];
            value = msg[1].value()

            if filter_if(key, value):
                k = key
                sortedrow = dict(sorted(value_serde.to_dict(value).items()))
                v = json.dumps(sortedrow)
                print(k + '=' + v)

    def get_records(self) -> Dict[Any, Message]:
        self.start(log_exception)
        records = self.await_get(5)
        self.stop()
        return records

    def __get_row(self, msg: Message, msg_to_list, filter_if, nometa):
        timestamp = msg.timestamp()
        headers = msg.headers()

        row = msg_to_list(msg)

        if not nometa:
            row_header = self.__get_row_header(headers, timestamp)
            row = row_header + row

        if filter_if(msg.key(), msg.value()):
            if not nometa:
                row = row_header + row
        else:
            row = None

        return row

    def __get_row_header(self, headers, timestamp):
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

    def __signal_handler(self, sig, frame):
        print('Stopping from Ctrl+C!')
        self.stop()


class JAWSProducer:
    """
        This class produces messages with the JAWS expected header.

        Sensible defaults are used to determine BOOTSTRAP_SERVERS (look in env)
        and to handle errors (log them).

        This producer also knows how to import records from a file using the JAWS expected file format.
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
