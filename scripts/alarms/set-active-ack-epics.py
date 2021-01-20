#!/usr/bin/env python3

import os
import pwd
import types
import click

# We can't use AvroProducer since it doesn't support string keys, see: https://github.com/confluentinc/confluent-kafka-python/issues/428
from confluent_kafka import avro, Producer
from confluent_kafka.avro import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer as AvroSerde
from avro.schema import Field

scriptpath = os.path.dirname(os.path.realpath(__file__))

with open(scriptpath + '/../../schemas/active-alarms-key.avsc', 'r') as file:
    key_schema_str = file.read()

with open(scriptpath + '/../../schemas/active-alarms-value.avsc', 'r') as file:
    value_schema_str = file.read()

key_schema = avro.loads(key_schema_str)
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

topic = 'active-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-active-ack-epics.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = serialize_avro(topic, value_schema, params.value, is_key=False)

    key_payload = serialize_avro(topic, key_schema, params.key, is_key=True)

    p.produce(topic=topic, value=val_payload, key=key_payload, headers=hdrs)
    p.flush()

@click.command()
@click.option('--ack', type=click.Choice(['MAJOR_ACK', 'MINOR_ACK', 'NO_ACK']), help="The alarm acknowledgement")
@click.argument('name')

def cli(ack, name):
    global params

    params = types.SimpleNamespace()

    params.key = {"name": name, "type": "AckEPICS"}

    if ack == None:
        raise click.ClickException(
            "Must specify option --ack")

    params.value = {"msg": {"ack": ack}}

    send()

cli()

