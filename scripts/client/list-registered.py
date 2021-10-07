#!/usr/bin/env python3

import os
import types
import click
import time
import json

from jlab_jaws.eventsource.table import EventSourceTable
from jlab_jaws.avro.serde import AlarmRegistrationSerde, AlarmClassSerde
from tabulate import tabulate
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.avro.entities import AlarmCategory

from common import get_row_header

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

alarms_key_deserializer = StringDeserializer('utf_8')
classes_key_deserializer = StringDeserializer('utf_8')

alarms_value_deserializer = AlarmRegistrationSerde.deserializer(schema_registry_client)
classes_value_deserializer = AlarmClassSerde.deserializer(schema_registry_client)

categories = AlarmCategory._member_names_


def alarms_get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:

        if value.alarm_class in classes:
            AlarmClassSerde.setClassDefaults(value, classes[value.alarm_class].value())

        row = [key,
               value.alarm_class,
               value.producer,
               value.location.name if value.location is not None else None,
               value.category.name if value.category is not None else None,
               value.priority.name if value.priority is not None else None,
               value.rationale,
               value.corrective_action,
               value.point_of_contact_username,
               value.latching,
               value.filterable,
               value.masked_by,
               value.screen_path]

    row_header = get_row_header(headers, timestamp)

    if params.category is None or (value is not None and params.category == value['category']):
        if not params.nometa:
            row = row_header + row
    else:
        row = None

    return row


def alarms_disp_table(records):
    head = ["Alarm Name", "Class", "Producer", "Location", "Category", "Priority", "Rationale", "Corrective Action",
            "P.O.C. Username", "Latching", "Filterable", "Masked By", "Screen Path"]
    table = []

    if not params.nometa:
        head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in records.values():
        row = alarms_get_row(msg)
        if row is not None:
            table.append(row)

    print(tabulate(table, head))


def classes_get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.location.name if value.location is not None else None,
               value.category.name if value.category is not None else None,
               value.priority.name if value.priority is not None else None,
               value.rationale,
               value.corrective_action,
               value.point_of_contact_username,
               value.latching,
               value.filterable,
               value.masked_by,
               value.screen_path]

    row_header = get_row_header(headers, timestamp)

    if params.category is None or (value is not None and params.category == value['category']):
        if not params.nometa:
            row = row_header + row
    else:
        row = None

    return row


def classes_disp_table(records):
    head = ["Class Name", "Location", "Category", "Priority", "Rationale", "Corrective Action",
            "P.O.C. Username", "Latching", "Filterable", "Masked By", "Screen Path"]
    table = []

    if not params.nometa:
        head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in records.values():
        row = classes_get_row(msg)
        if row is not None:
            table.append(row)

    print(tabulate(table, head))


def alarms_export(records):
    for msg in records.values():
        key = msg.key()
        value = msg.value()

        if params.category is None or (value is not None and params.category == value['category']):
            v = json.dumps(AlarmRegistrationSerde.to_dict(value))
            print(key + '=' + v)


def classes_export(records):
    for msg in records.values():
        key = msg.key()
        value = msg.value()

        if params.category is None or (value is not None and params.category == value['category']):
            k = key
            v = json.dumps(AlarmClassSerde.to_dict(value))
            print(k + '=' + v)


def alarms_initial_state(records):
    if params.export:
        alarms_export(records)
    else:
        alarms_disp_table(records)


def alarms_state_update(record):
    row = alarms_get_row(record)
    print(row)


classes = {}


def classes_initial_state(records):
    global classes

    if params.display == 'alarms_with_class_defaults':
        for record in records.values():
            classes[record.key()] = record
        list_alarms()
    elif params.export:
        classes_export(records)
    else:
        classes_disp_table(records)


def classes_state_update(record):
    if params.display == 'alarms_with_class_defaults':
        classes[record.key().alarm_class.name] = record
    else:
        row = classes_get_row(record)
        print(row)


def list_alarms():
    ts = time.time()

    config = {'topic': 'alarm-registrations',
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': alarms_key_deserializer,
              'value.deserializer': alarms_value_deserializer,
              'group.id': 'list-registered.py' + str(ts)}
    etable = EventSourceTable(config, alarms_initial_state, alarms_state_update)
    etable.start()


def list_classes():
    ts = time.time()

    config = {'topic': 'alarm-classes',
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': classes_key_deserializer,
              'value.deserializer': classes_value_deserializer,
              'group.id': 'list-registered.py' + str(ts)}
    etable = EventSourceTable(config, classes_initial_state, classes_state_update)
    etable.start()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True,
              help="Dump records in AVRO JSON format such that they can be imported by set-registered.py; implies --nometa")
@click.option('--category', type=click.Choice(categories), help="Only show registered alarms in the specified category")
@click.option('--display', default="alarms_with_class_defaults",  type=click.Choice(["alarms", "classes", "alarms_with_class_defaults"]), help="Whether to display alarms, classes, or alarms with class defaults applied")
def cli(monitor, nometa, export, category, display):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export
    params.category = category
    params.display = display

    if display == 'alarms':
        list_alarms()
    else:
        list_classes()


cli()
