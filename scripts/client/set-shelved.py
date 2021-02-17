#!/usr/bin/env python3

import os
import pwd
import types
import click
import time

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

with open(projectpath + '/config/subject-schemas/shelved-alarms-value.avsc', 'r') as file:
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

avro_serializer = AvroSerializer(value_schema_str,
                                 schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': StringSerializer('utf_8'),
                 'value.serializer': avro_serializer}
producer = SerializingProducer(producer_conf)

topic = 'shelved-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-shelved.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = params.value

    producer.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()

@click.command()
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--expirationseconds', type=int, help="The number of seconds until the shelved status expires, None for indefinite")
@click.option('--reason', help="The explanation for why this alarm has been shelved")
@click.argument('name')

def cli(unset, expirationseconds, reason, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

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

        params.value = {"expiration": timestampMillis, "reason": reason}

    send()

cli()

