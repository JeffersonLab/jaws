#!/usr/bin/env python3

import os
import pwd
import types
import click
import time

# We can't use AvroProducer since it doesn't support string keys, see: https://github.com/confluentinc/confluent-kafka-python/issues/428
from confluent_kafka import avro, Producer
from confluent_kafka.avro import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer as AvroSerde
from avro.schema import Field

scriptpath = os.path.dirname(os.path.realpath(__file__))

with open(scriptpath + '/../../schemas/shelved-alarms-value.avsc', 'r') as file:
    value_schema_str = file.read()

value_schema = avro.loads(value_schema_str)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered')

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry = CachedSchemaRegistryClient(conf)

avro_serde = AvroSerde(schema_registry)
serialize_avro = avro_serde.encode_record_with_schema

p = Producer({
    'bootstrap.servers': bootstrap_servers,
    'on_delivery': delivery_report})

topic = 'shelved-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-shelved.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = serialize_avro(topic, value_schema, params.value, is_key=False)

    p.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs)
    p.flush()

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

