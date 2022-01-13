#!/usr/bin/env python3

import os
import types
import click
import time

from jlab_jaws.eventsource.cached_table import ActivationCachedTable
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.avro.serde import AlarmActivationUnionSerde
from jlab_jaws.eventsource.table import EventSourceTable
from tabulate import tabulate

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
               value]

    row_header = get_row_header(headers, timestamp)

    row = row_header + row

    return row


def disp_table(records):
    head = ["Alarm Name", "Value"]
    table = []

    head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in records.values():
        row = get_row(msg)
        if row is not None:
            table.append(row)

    print(tabulate(table, head))


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
def cli(monitor):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.export = False
    params.disp_table = disp_table

    etable = ActivationCachedTable(bootstrap_servers, schema_registry_client)

    ShellTable(etable, params)


cli()
