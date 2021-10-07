#!/usr/bin/env python3

import os
import pwd
import types
import click

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.entities import Alarm, AlarmState, AlarmOverrideSet, ProcessorTransitions
from jlab_jaws.avro.serde import AlarmSerde

from common import delivery_report

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = StringSerializer()
value_serializer = AlarmSerde.serializer(schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-alarms.py'),('host',os.uname().nodename)]


def send():
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


@click.command()
@click.option('--unset', is_flag=True, help="present to clear state, missing to set state")
@click.option('--state', required=True, type=click.Choice(AlarmState._member_names_), help="The state")
@click.argument('name')
def cli(unset, state, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if unset:
        params.value = None
    else:
        params.value = Alarm(None,
                             None,
                             None,
                             None,
                             AlarmOverrideSet(None, None, None, None, None, None, None),
                             ProcessorTransitions(False, False, False, False,
                                                  False, False, False, False),
                             AlarmState[state])

    send()


cli()
