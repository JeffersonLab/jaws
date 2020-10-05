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

value_schema_str = """
{
   "namespace" : "org.jlab.kafka.alarms",
   "name"      : "ActiveAlarm",
   "type"      : "record",
   "fields"    : [
     {
       "name"    : "priority",
       "type"    : {
         "name"    : "AlarmPriority",
         "type"    : "enum",
         "symbols" : ["P1_LIFE","P2_PROPERTY","P3_PRODUCTIVITY", "P4_DIAGNOSTIC"],
         "doc"     : "Alarm severity organized as a way for operators to prioritize which alarms to take action on first"
       }
     },
     {
        "name"    : "acknowledged",
        "type"    : "boolean",
        "default" : false,
        "doc"     : "Indicates whether this alarm has been explicitly acknowledged - useful for latching alarms which can only be cleared after acknowledgement"
     }
  ]
}
"""

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

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-active.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = serialize_avro(topic, value_schema, params.value, is_key=False)

    p.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs)
    p.flush()

@click.command()
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--priority', type=click.Choice(['P1_LIFE', 'P2_PROPERTY', 'P3_PRODUCTIVITY', 'P4_DIAGNOSTIC']), help="The alarm serverity as a priority for operators")
@click.option('--ack', is_flag=True, help="Acknowledge the alarm")
@click.argument('name')

def cli(unset, priority, ack, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if unset:
        params.value = None
    else:
        if priority == None:
            raise click.ClickException(
                    "Must specify option --priority")

        params.value = {"priority": priority, "acknowledged": ack}

    send()

cli()

