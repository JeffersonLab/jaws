#!/usr/bin/env python3

import os
import pkgutil
import types
import click
import time
import json

from json import loads
from jlab_jaws.serde.avro import AvroDeserializerWithReferences
from jlab_jaws.eventsource.table import EventSourceTable
from tabulate import tabulate
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringDeserializer
from fastavro import parse_schema

class_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmClass.avsc")
class_schema_str = class_bytes.decode('utf-8')

location_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmLocation.avsc")
location_schema_str = location_bytes.decode('utf-8')

category_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmCategory.avsc")
category_schema_str = category_bytes.decode('utf-8')

priority_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmPriority.avsc")
priority_schema_str = priority_bytes.decode('utf-8')

value_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/registered-alarms-value.avsc")
value_schema_str = value_bytes.decode('utf-8')

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

named_schemas = {}
ref_dict = loads(class_schema_str)
parse_schema(ref_dict, named_schemas=named_schemas)
ref_dict = loads(location_schema_str)
parse_schema(ref_dict, named_schemas=named_schemas)
ref_dict = loads(category_schema_str)
parse_schema(ref_dict, named_schemas=named_schemas)
ref_dict = loads(priority_schema_str)
parse_schema(ref_dict, named_schemas=named_schemas)

avro_deserializer = AvroDeserializerWithReferences(schema_registry_client, None, None, True, named_schemas)
string_deserializer = StringDeserializer('utf_8')

ts = time.time()


def disp_row(msg):
    row = get_row(msg)
    if row is not None:
        print(row)  # TODO: format with a row template!


def disp_ref(ref):
    if ref is not None:
        result = ref[1]
    else:
        result = None
    return result


def get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    row = [key,
           value["class"],
           value["producer"],
           disp_ref(value["location"]),
           disp_ref(value["category"]),
           disp_ref(value["priority"]),
           value["rationale"],
           value["correctiveaction"],
           value["pointofcontactusername"],
           value["latching"],
           value["filterable"],
           value["maskedby"],
           value["screenpath"]]

    ts = time.ctime(timestamp[1] / 1000)

    user = ''
    producer = ''
    host = ''

    if headers is not None:
        lookup = dict(headers)
        bytez = lookup.get('user', b'')
        user = bytez.decode()
        bytez = lookup.get('producer', b'')
        producer = bytez.decode()
        bytez = lookup.get('host', b'')
        host = bytez.decode()

    if params.category is None or (value is not None and params.category == value['category']):
        if not params.nometa:
            row = [ts, user, host, producer] + row
    else:
        row = None

    return row


def disp_table():
    head = ["Alarm Name", "Class", "Producer", "Location", "Category", "Priority", "Rationale", "Corrective Action",
            "P.O.C. Username", "Latching", "Filterable", "Masked By", "Screen Path"]
    table = []

    if not params.nometa:
        head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in registered.values():
        row = get_row(msg)
        if row is not None:
            table.append(row)

    print(tabulate(table, head))


def export():
    for msg in registered.values():
        key = msg.key()
        value = msg.value()

        if params.category is None or (value is not None and params.category == value['category']):
            v = json.dumps(value)
            print(key + '=' + v)


registered = {}


def handle_initial_state(records):
    global registered

    registered = records

    if params.export:
        export()
    else:
        disp_table()


def handle_state_update(records):
    disp_row(records)


def list_records():
    config = {'topic': 'registered-alarms',
              'monitor': params.monitor,
              'bootstrap.servers': bootstrap_servers,
              'key.deserializer': string_deserializer,
              'value.deserializer': avro_deserializer,
              'group.id': 'list-registered.py' + str(ts)}
    EventSourceTable(config, handle_initial_state, handle_state_update)


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True,
              help="Dump records in AVRO JSON format such that they can be imported by set-registered.py; implies --nometa")
@click.option('--category', help="Only show registered alarms in the specified category")
def cli(monitor, nometa, export, category):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export
    params.category = category

    list_records()


cli()
