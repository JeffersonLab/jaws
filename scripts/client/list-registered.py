#!/usr/bin/env python3

import os
import types
import click
import time
import json

from tabulate import tabulate

from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer, SerializationError
from confluent_kafka import OFFSET_BEGINNING

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

with open(projectpath + '/config/subject-schemas/registered-alarms-value.avsc', 'r') as file:
    value_schema_str = file.read()

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

avro_deserializer = AvroDeserializer(value_schema_str,
                                     schema_registry_client)
string_deserializer = StringDeserializer('utf_8')

ts = time.time()

consumer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.deserializer': string_deserializer,
                 'value.deserializer': avro_deserializer,
                 'group.id': 'list-registered.py' + str(ts)}


registered = {}

empty = False

def my_on_assign(consumer, partitions):
    # We are assuming one partition, otherwise low/high would each be array and checking against high water mark would probably not work since other partitions could still contain unread messages.
    global low
    global high
    global empty
    for p in partitions:
        p.offset = OFFSET_BEGINNING
        low, high = consumer.get_watermark_offsets(p)
        if high == 0:
            empty = True
    consumer.assign(partitions)

def disp_row(msg):
    row = get_row(msg)
    if(row is not None):
        print(row) # TODO: format with a row template!

def get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    row = [key, value["producer"], value["location"], value["category"], value["priority"], value["rationale"], value["correctiveaction"], value["pointofcontactfirstname"], value["pointofcontactlastname"], value["pointofcontactemail"], value["latching"], value["filterable"], value["maskedby"], value["screenpath"]]

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

    head=["Alarm Name", "Producer", "Location", "Category", "Priority", "Rationale", "Corrective Action", "P.O.C. Firstname", "P.O.C. Lastname", "P.O.C. email", "Latching", "Filterable", "Masked By", "Screen Path"]
    table = []

    if not params.nometa:
        head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in registered.values():
        row = get_row(msg)
        if(row is not None):
            table.append(row)

    print(tabulate(table, head))


def export():
    for msg in registered.values():
        key = msg.key()
        value = msg.value()
   
        if params.category is None or (value is not None and params.category == value['category']):
            v = json.dumps(value)
            print(key + '=' + v)

def list():
    c = DeserializingConsumer(consumer_conf)

    c.subscribe(['registered-alarms'], on_assign=my_on_assign)

    while True:
        try:
            msg = c.poll(1.0)

        except SerializationError as e:
            print("Message deserialization failed for {}: {}".format(msg, e))
            break

        if empty:
            break

        if msg is None:
            continue

        if msg.error():
            print("AvroConsumer error: {}".format(msg.error()))
            continue

        if msg.value() is None:
            del registered[msg.key()]
        else:
            registered[msg.key()] = msg

        if msg.offset() + 1 == high:
            break

    if params.export:
        export()
    else:
        disp_table()

    if params.monitor:
        while True:
            try:
                msg = c.poll(1.0)

            except SerializationError as e:
                print("Message deserialization failed for {}: {}".format(msg, e))
                break

            if msg is None:
                continue

            if msg.error():
                print("AvroConsumer error: {}".format(msg.error()))
                continue

            disp_row(msg)

    c.close()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format such that they can be imported by set-registered.py; implies --nometa")
@click.option('--category', help="Only show registered alarms in the specified category")

def cli(monitor, nometa, export, category):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export
    params.category = category

    list()

cli()
