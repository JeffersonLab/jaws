#!/usr/bin/env python3

import os
import types
import click
import time
import json

from jlab_jaws.eventsource.table import EventSourceTable
from tabulate import tabulate
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer

from common import get_row_header

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_deserializer = StringDeserializer('utf_8')

value_deserializer = StringDeserializer('utf_8')


def get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    if value is not None:
        row = [key]
    else:
        row = [None]

    if not params.nometa:
        row_header = get_row_header(headers, timestamp)
        row = row_header + row

    return row


def disp_table(records):
    head = ["Category"]

    table = []

    if not params.nometa:
        head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in records.values():
        row = get_row(msg)
        if row is not None:
            table.append(row)

    # Truncate long cells
    table = [[(c if len(str(c)) < 20 else str(c)[:17] + "...") for c in row] for row in table]

    print(tabulate(table, head))


def export(records):
    sortedtable = sorted(records.items())

    for msg in sortedtable:
        key = msg[0];
        value = msg[1].value()

        sortedrow = dict(sorted(value).items())
        v = json.dumps(sortedrow)
        print(key + '=' + v)


def initial_state(records):
    if params.export:
        export(records)
    else:
       disp_table(records)


def state_update(record):
    row = get_row(record)
    print(row)


def list_records():
    ts = time.time()

    config = {'topic': 'alarm-categories',
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': key_deserializer,
              'value.deserializer': value_deserializer,
              'group.id': 'list-categories.py' + str(ts)}
    etable = EventSourceTable(config, initial_state, state_update)
    etable.start()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True,
              help="Dump records in AVRO JSON format such that they can be imported by set-category.py; implies --nometa")
def cli(monitor, nometa, export):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export

    list_records()


cli()
