#!/usr/bin/env python3

import os

import pwd
import types
import click
import json

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.avro.entities import AlarmLocation
from jlab_jaws.avro.serde import AlarmLocationSerde

from common import delivery_report, set_log_level_from_env

set_log_level_from_env()

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = StringSerializer('utf_8')
value_serializer = AlarmLocationSerde.serializer(schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'alarm-locations'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name), ('producer', 'set-location.py'), ('host', os.uname().nodename)]


def send():
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


def import_records(file):
    print("Loading file", file)
    handle = open(file, 'r')
    lines = handle.readlines()

    for line in lines:
        tokens = line.split("=", 1)
        key = tokens[0]
        value_obj = tokens[1]
        value_dict = json.loads(value_obj)
        print("{}={}".format(key, value_dict))

        value = AlarmLocationSerde.from_dict(value_dict)

        producer.produce(topic=topic, value=value, key=key, headers=hdrs, on_delivery=delivery_report)

    producer.flush()


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is location name and value is JSON "
                   "with parent field")
@click.option('--unset', is_flag=True, help="Remove the location")
@click.argument('name')
@click.option('--parent', '-p', help="Name of parent Location or None if top-level Location")
def cli(file, unset, name, parent):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if file:
        import_records(name)
    else:
        if unset:
            params.value = None
        else:
            params.value = AlarmLocation(parent)

        send()


cli()
