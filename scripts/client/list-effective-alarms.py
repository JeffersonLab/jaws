#!/usr/bin/env python3

import os
import types
import click

from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.eventsource.cached_table import EffectiveAlarmCachedTable
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
    params.export = False
    params.disp_table = disp_table

    etable = EffectiveAlarmCachedTable(bootstrap_servers, schema_registry_client)

    ShellTable(etable, params)


cli()
