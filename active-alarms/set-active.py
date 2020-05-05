#!/usr/bin/env python3

import os
import types
import click

# We can't use AvroProducer since it doesn't support string keys, see: https://github.com/confluentinc/confluent-kafka-python/issues/428
from confluent_kafka import avro, Producer
from confluent_kafka.avro import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer as AvroSerde
from avro.schema import Field

Field.to_json_old = Field.to_json

# Fixes an issue with python3-avro:
# https://github.com/confluentinc/confluent-kafka-python/issues/610
def to_json(self, names=None):
    to_dump = self.to_json_old(names)
    type_name = type(to_dump["type"]).__name__
    if type_name == "mappingproxy":
        to_dump["type"] = to_dump["type"].copy()
    return to_dump


Field.to_json = to_json

value_schema_str = """
{
   "namespace" : "org.jlab",
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

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = serialize_avro(topic, value_schema, params.value, is_key=False)

    p.produce(topic=topic, value=val_payload, key=params.key)
    p.flush()

@click.command()
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--priority', type=click.Choice(['P1_LIFE', 'P2_PROPERTY', 'P3_PRODUCTIVITY', 'P4_DIAGNOSTIC']), help="The alarm serverity as a priority for operators")
@click.argument('name')

def cli(unset, priority, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if unset:
        params.value = None
    else:
        if priority == None:
            raise click.ClickException(
                    "Must specify option --priority")

        params.value = {"priority": priority}

    send()

cli()

