import logging
import os
import signal
from typing import Dict, Any

import time
from confluent_kafka.cimpl import Message
from jlab_jaws.eventsource.cached_table import CachedTable, log_exception
from jlab_jaws.eventsource.listener import EventSourceListener
from jlab_jaws.eventsource.table import TimeoutException


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


def set_log_level_from_env():
    level = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S')


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


def delivery_report(err, msg):
    if err is not None:
        logging.error('Failed: {}'.format(err))
    else:
        logging.debug('Delivered')
