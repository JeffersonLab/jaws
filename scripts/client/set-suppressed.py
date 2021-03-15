#!/usr/bin/env python3

import os
import pwd
import types
import click
import time

import avro.schema

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

with open(projectpath + '/config/subject-schemas/suppressed-alarms-key.avsc', 'r') as file:
    key_schema_str = file.read()

with open(projectpath + '/config/subject-schemas/suppressed-alarms-value.avsc', 'r') as file:
    value_schema_str = file.read()

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered')

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = AvroSerializer(key_schema_str,
                                  schema_registry_client)

value_serializer = AvroSerializer(value_schema_str,
                                 schema_registry_client)

value_schema = avro.schema.Parse(value_schema_str)

reasons = value_schema.fields[0].type.schemas[2].fields[1].type.symbols

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'suppressed-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-suppressed.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = params.value

    producer.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()

@click.command()
@click.option('--unset', is_flag=True, help="Remove the suppression")
@click.option('--expirationseconds', type=int, help="The number of seconds until the shelved status expires, None for indefinite")
@click.option('--reason', type=click.Choice(reasons), help="The explanation for why this alarm has been shelved")
@click.option('--comments', help="Operator explanation for why suppressed")
@click.argument('name')

def cli(unset, expirationseconds, reason, comments, name):
    global params

    params = types.SimpleNamespace()

    params.key = {"name": name, "type": "Shelved"}

    if unset:
        params.value = None
    else:
        if reason == None:
            raise click.ClickException("--reason is required")

        if expirationseconds == None:
            timestampMillis = None
        else:
            timestampSeconds = time.time() + expirationseconds;
            timestampMillis = int(timestampSeconds * 1000);

        params.value = {"msg": {"reason": reason, "comments": comments, "expiration": timestampMillis}}

        print(params.value)

    send()

cli()

