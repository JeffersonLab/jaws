#!/usr/bin/env python3

import os
import types
import click
import json

from jlab_jaws.avro.serde import AlarmLocationSerde
from jlab_jaws.eventsource.cached_table import LocationCachedTable
from tabulate import tabulate
from confluent_kafka.schema_registry import SchemaRegistryClient

from common import get_row_header, ShellTable

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)


def get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.parent]

    row_header = get_row_header(headers, timestamp)

    if not params.nometa:
        row = row_header + row

    return row


def disp_table(records):
    head = ["Location", "Parent"]
    table = []

    if not params.nometa:
        head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in records.values():
        row = get_row(msg)
        if row is not None:
            table.append(row)

    # Truncate long cells
    table = [[(c if len(str(c)) < 30 else str(c)[:27] + "...") for c in row] for row in table]

    print(tabulate(table, head))


def export_msgs(records):
    sortedtable = sorted(records.items())

    for msg in sortedtable:
        key = msg[0];
        value = msg[1].value()

        k = key
        sortedrow = dict(sorted(AlarmLocationSerde.to_dict(value).items()))
        v = json.dumps(sortedrow)
        print(k + '=' + v)


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True,
              help="Dump records in AVRO JSON format such that they can be imported by set-location.py; implies "
                   "--nometa")
def cli(monitor, nometa, export):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export
    params.export_msgs = export_msgs
    params.disp_table = disp_table

    table = LocationCachedTable(bootstrap_servers, schema_registry_client)

    ShellTable(table, params)


cli()
