#!/usr/bin/env python3

import os
import types
import click
import time
import json

from jlab_jaws.eventsource.table import EventSourceTable
from jlab_jaws.avro.serde import AlarmInstanceSerde
from tabulate import tabulate
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.avro.entities import AlarmCategory, UnionEncoding

from common import get_row_header

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

registrations_key_deserializer = StringDeserializer('utf_8')

registrations_value_deserializer = AlarmInstanceSerde.deserializer(schema_registry_client)

categories = AlarmCategory._member_names_


def registrations_get_row(msg):
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
                       value.alarm_class,
                       value.producer,
                       value.location.name if value.location is not None else None,
                       value.category.name if value.category is not None else None,
                       value.priority.name if value.priority is not None else None,
                       value.rationale.replace("\n", "\\n") if value.rationale is not None else None,
                       value.corrective_action.replace("\n", "\\n ") if value.corrective_action is not None else None,
                       value.point_of_contact_username,
                       value.latching,
                       value.filterable,
                       value.masked_by,
                       value.screen_path]

            if not params.nometa:
                row_header = get_row_header(headers, timestamp)
                row = row_header + row

    return row


def registrations_disp_table(records):
    head = ["Alarm Name", "Class", "Producer", "Location", "Category", "Priority", "Rationale", "Corrective Action",
            "P.O.C. Username", "Latching", "Filterable", "Masked By", "Screen Path"]
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

        if params.category is None or (value is not None and params.category == value.category.name):
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
    ts = time.time()

    config = {'topic': 'alarm-instances',
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': registrations_key_deserializer,
              'value.deserializer': registrations_value_deserializer,
              'group.id': 'list-instances.py' + str(ts)}
    etable = EventSourceTable(config, registrations_initial_state, registrations_state_update)
    etable.start()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True,
              help="Dump records in AVRO JSON format such that they can be imported by set-instance.py; implies --nometa")
@click.option('--category', type=click.Choice(categories), help="Only show registrations in the specified category")
@click.option('--alarm_class', help="Only show registrations in the specified class")
def cli(monitor, nometa, export, category, alarm_class):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export
    params.category = category
    params.alarm_class = alarm_class

    list_registrations()


cli()
