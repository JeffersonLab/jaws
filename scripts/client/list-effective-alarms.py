#!/usr/bin/env python3

import os
import types
import click
import time

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.avro.serde import EffectiveAlarmSerde
from jlab_jaws.eventsource.table import EventSourceTable
from tabulate import tabulate

from common import get_row_header

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_deserializer = StringDeserializer()
value_deserializer = EffectiveAlarmSerde.deserializer(schema_registry_client)


def get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.activation.state.name]

        if params.overrides:
            row.append(value.activation.overrides)

        if params.registration:
            row.append(value.registration.calculated)

    row_header = get_row_header(headers, timestamp)

    row = row_header + row

    return row


def disp_table(records):
    head = ["Alarm Name", "State"]
    table = []

    if params.overrides:
        head.append("Overrides")

    if params.registration:
        head.append("Effective Registration")

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

    config = {'topic': 'effective-alarms',
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': key_deserializer,
              'value.deserializer': value_deserializer,
              'group.id': 'list-effective-alarms.py' + str(ts)}
    etable = EventSourceTable(config, handle_initial_state, handle_state_update)
    etable.start()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--overrides', is_flag=True, help="Show overrides")
@click.option('--registration', is_flag=True, help="Show effective registration")
def cli(monitor, overrides, registration):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.overrides = overrides
    params.registration = registration

    list_records()


cli()
