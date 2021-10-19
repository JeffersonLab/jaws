#!/usr/bin/env python3

import os
import pwd
import types
import click
import time

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.entities import EffectiveRegistration, \
    AlarmRegistration, AlarmLocation, AlarmCategory, AlarmPriority, SimpleProducer
from jlab_jaws.avro.serde import EffectiveRegistrationSerde

from common import delivery_report

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

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name), ('producer', 'set-effective-registrations.py'),
        ('host', os.uname().nodename)]


def send():
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


def get_effective_registration():
    return AlarmRegistration(AlarmLocation.INJ,
                             AlarmCategory.RF,
                             AlarmPriority.P4_INCIDENTAL,
                             "testing",
                             "fix it",
                             "tester",
                             True,
                             True,
                             5,
                             5,
                             "alarm1",
                             "/tmp",
                             "base",
                             SimpleProducer())


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
        actual_reg = get_effective_registration()
        calculated_reg = get_effective_registration()

        params.value = EffectiveRegistration(alarm_class, actual_reg, calculated_reg)

    send()


cli()
