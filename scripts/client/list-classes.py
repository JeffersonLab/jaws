#!/usr/bin/env python3

import os
import types
import click
import json

from jlab_jaws.eventsource.cached_table import ClassCachedTable, CategoryCachedTable, log_exception
from jlab_jaws.avro.serde import AlarmClassSerde
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
               value.category,
               value.priority.name if value.priority is not None else None,
               value.rationale.replace("\n", "\\n ") if value.rationale is not None else None,
               value.corrective_action.replace("\n", "\\n") if value.corrective_action is not None else None,
               value.point_of_contact_username,
               value.latching,
               value.filterable,
               value.screen_path]

    row_header = get_row_header(headers, timestamp)

    if params.category is None or (value is not None and params.category == value.category):
        if not params.nometa:
            row = row_header + row
    else:
        row = None

    return row


def disp_table(records):
    head = ["Class Name", "Category", "Priority", "Rationale", "Corrective Action",
            "P.O.C. Username", "Latching", "Filterable", "Screen Path"]
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


def export_msgs(records):
    sortedtable = sorted(records.items())

    for msg in sortedtable:
        key = msg[0];
        value = msg[1].value()

        if params.category is None or (value is not None and params.category == value.category):
            k = key
            sortedrow = dict(sorted(AlarmClassSerde.to_dict(value).items()))
            v = json.dumps(sortedrow)
            print(k + '=' + v)


categories_table = CategoryCachedTable(bootstrap_servers)
categories_table.start(log_exception)
categories = categories_table.await_get(5).values()
categories_table.stop()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True,
              help="Dump records in AVRO JSON format such that they can be imported by set-class.py; implies --nometa")
@click.option('--category', type=click.Choice(categories), help="Only show registered alarms in the specified category")
def cli(monitor, nometa, export, category):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export
    params.category = category
    params.export_msgs = export_msgs
    params.disp_table = disp_table

    etable = ClassCachedTable(bootstrap_servers, schema_registry_client)

    ShellTable(etable, params)


cli()
