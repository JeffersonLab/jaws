#!/usr/bin/env python3

import os
import types
import click

from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.eventsource.cached_table import CategoryCachedTable, EffectiveRegistrationCachedTable, log_exception
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


categories_table = CategoryCachedTable(bootstrap_servers)
categories_table.start(log_exception)
categories = categories_table.await_get(5).values()
categories_table.stop()


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
    params.export = False
    params.disp_table = disp_table

    etable = EffectiveRegistrationCachedTable(bootstrap_servers, schema_registry_client)

    ShellTable(etable, params)


cli()
