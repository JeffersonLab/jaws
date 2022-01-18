#!/usr/bin/env python3

import os

import pwd
import types
import click

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient

from common import delivery_report

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = StringSerializer('utf_8')
value_serializer = StringSerializer('utf_8')

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'alarm-categories'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name), ('producer', 'set-category.py'), ('host', os.uname().nodename)]


def send():
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


def import_records(file):
    print("Loading file", file)
    handle = open(file, 'r')
    lines = handle.readlines()

    for line in lines:
        key = line.rstrip()
        value = ""

        producer.produce(topic=topic, value=value, key=key, headers=hdrs)

    producer.flush()


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is category name and value is empty string")
@click.option('--unset', is_flag=True, help="Remove the category")
@click.argument('name')
def cli(file, unset, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if file:
        import_records(name)
    else:
        if unset:
            params.value = None
        else:
            params.value = ""

        send()


cli()
