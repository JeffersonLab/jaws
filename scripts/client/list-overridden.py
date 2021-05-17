#!/usr/bin/env python3

import os
import types
import click
import time

from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.avro.subject_schemas.serde import OverriddenAlarmKeySerde, OverriddenAlarmValueSerde
from jlab_jaws.eventsource.table import EventSourceTable
from tabulate import tabulate

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)


key_deserializer = OverriddenAlarmKeySerde.deserializer(schema_registry_client)
value_deserializer = OverriddenAlarmValueSerde.deserializer(schema_registry_client)


def get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key.name, key.type, None]
    else:
        row = [key.name,
               key.type.name,
               value]

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

    row = [ts, user, host, producer] + row

    return row


def disp_table(records):
    head = ["Alarm Name", "Override Type", "Value"]
    table = []

    head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in records.values():
        row = get_row(msg)
        if row is not None:
            table.append(row)

    print(tabulate(table, head))


def handle_initial_state(records):
    disp_table(records)


def handle_state_update(record):
    row = get_row(record)
    print(row)


def list_records():
    ts = time.time()

    config = {'topic': "overridden-alarms",
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': key_deserializer,
              'value.deserializer': value_deserializer,
              'group.id': 'list-overridden.py' + str(ts)}
    EventSourceTable(config, handle_initial_state, handle_state_update)


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
def cli(monitor):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor

    list_records()


cli()
