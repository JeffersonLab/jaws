#!/usr/bin/env python3

import os
import types
import click
import time

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.avro.subject_schemas.serde import ActiveAlarmSerde
from jlab_jaws.eventsource.table import EventSourceTable

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_deserializer = StringDeserializer()
value_deserializer = ActiveAlarmSerde.deserializer(schema_registry_client)


def disp_msg(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

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

    print(ts, '|', user, '|', producer, '|', host, '|', key, '=', value)


def disp_table(records):
    for record in records:
        disp_row(record)


def disp_row(record):
    disp_msg(record)


def handle_initial_state(records):
    disp_table(records.values())


def handle_state_update(records):
    disp_row(records.values())


def list_records():
    ts = time.time()

    config = {'topic': params.topic,
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': key_deserializer,
              'value.deserializer': value_deserializer,
              'group.id': 'list-active.py' + str(ts)}
    EventSourceTable(config, handle_initial_state, handle_state_update)

@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--topic', default='active-alarms', help="Topic to read from (used to switch between filtered views)")

def cli(monitor, topic):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.topic = topic

    list_records()

cli()