#!/usr/bin/env python3

import os
import types
import click
import json

from jlab_jaws.eventsource.cached_table import InstanceCachedTable
from jlab_jaws.avro.serde import AlarmInstanceSerde
from jlab_jaws.eventsource.table import TimeoutException
from tabulate import tabulate
from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.avro.entities import UnionEncoding

from common import get_row_header

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

def registrations_get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    row = None

    if params.alarm_class is None or (value is not None and params.alarm_class == value.alarm_class):
        if value is None:
            row = [key, None]
        else:
            row = [key,
                   value.alarm_class,
                   value.producer,
                   value.location,
                   value.masked_by,
                   value.screen_path]

        if not params.nometa:
            row_header = get_row_header(headers, timestamp)
            row = row_header + row

    return row


def registrations_disp_table(records):
    head = ["Alarm Name", "Class", "Producer", "Location",
            "Masked By", "Screen Path"]
    table = []

    if not params.nometa:
        head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in records.values():
        row = registrations_get_row(msg)
        if row is not None:
            table.append(row)

    # Truncate long cells
    table = [[(c if len(str(c)) < 20 else str(c)[:17] + "...") for c in row] for row in table]

    print(tabulate(table, head))


def registrations_export(records):
    sortedtable = sorted(records.items())

    for msg in sortedtable:
        key = msg[0];
        value = msg[1].value()

        if params.alarm_class is None or (value is not None and params.alarm_class == value.alarm_class):
            sortedrow = dict(sorted(AlarmInstanceSerde.to_dict(value, UnionEncoding.DICT_WITH_TYPE).items()))
            v = json.dumps(sortedrow)
            print(key + '=' + v)


def registrations_initial_state(records):
    if params.export:
        registrations_export(records)
    else:
        registrations_disp_table(records)


def registrations_state_update(record):
    row = registrations_get_row(record)
    print(row)


def list_registrations():
    etable = InstanceCachedTable(bootstrap_servers, schema_registry_client)

    try:
        msgs = etable.await_get(5)
    except TimeoutException:
        print("Took too long to obtain list")


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True,
              help="Dump records in AVRO JSON format such that they can be imported by set-instance.py; implies --nometa")
@click.option('--alarm_class', help="Only show instances in the specified class")
def cli(monitor, nometa, export, alarm_class):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export
    params.alarm_class = alarm_class

    list_registrations()


cli()
