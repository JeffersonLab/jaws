#!/usr/bin/env python3

import os
import pwd
import types
import click

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.entities import EffectiveRegistration, \
    AlarmInstance, SimpleProducer
from jlab_jaws.avro.serde import EffectiveRegistrationSerde

from common import delivery_report, set_log_level_from_env

set_log_level_from_env()

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = StringSerializer()
value_serializer = EffectiveRegistrationSerde.serializer(schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'effective-registrations'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name), ('producer', 'set-effective-registration.py'),
        ('host', os.uname().nodename)]


def send():
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


def get_instance():
    return AlarmInstance("base",
                         SimpleProducer(),
                         ["INJ"],
                         "alarm1",
                         "command1")


@click.command()
@click.option('--unset', is_flag=True, help="present to clear state, missing to set state")
@click.argument('name')
def cli(unset, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if unset:
        params.value = None
    else:
        alarm_class = None
        alarm_instance = get_instance()

        params.value = EffectiveRegistration(alarm_class, alarm_instance)

    send()


cli()
