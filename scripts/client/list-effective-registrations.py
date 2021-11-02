#!/usr/bin/env python3

import os
import types
import click
import time

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.avro.serde import EffectiveRegistrationSerde
from jlab_jaws.eventsource.table import EventSourceTable
from jlab_jaws.avro.entities import AlarmCategory
from tabulate import tabulate

from common import get_row_header

categories = AlarmCategory._member_names_

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_deserializer = StringDeserializer()
value_deserializer = EffectiveRegistrationSerde.deserializer(schema_registry_client)


def get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    row = None

    if params.category is None or (value is not None and params.category == value.category.name):
        if params.alarm_class is None or (value is not None and params.alarm_class == value.alarm_class):
            if value is None:
                row = [key, None]
            else:
                row = [key,
                       value.calculated]

            if not params.nometa:
                row_header = get_row_header(headers, timestamp)
                row = row_header + row

    return row


def disp_table(records):
    head = ["Alarm Name", "Effective Registration"]
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

    config = {'topic': 'effective-registrations',
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': key_deserializer,
              'value.deserializer': value_deserializer,
              'group.id': 'list-effective-registrations.py' + str(ts)}
    etable = EventSourceTable(config, handle_initial_state, handle_state_update)
    etable.start()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--category', type=click.Choice(categories), help="Only show registrations in the specified category")
@click.option('--alarm_class', help="Only show registrations in the specified class")
def cli(monitor, nometa, category, alarm_class):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.category = category
    params.alarm_class = alarm_class

    list_records()


cli()
