#!/usr/bin/env python3

import click

from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.entities import EffectiveRegistration, \
    AlarmInstance, SimpleProducer
from jlab_jaws.avro.serde import EffectiveRegistrationSerde

from common import get_registry_client, JAWSProducer


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
    schema_registry_client = get_registry_client()

    key_serializer = StringSerializer()
    value_serializer = EffectiveRegistrationSerde.serializer(schema_registry_client)

    producer = JAWSProducer('effective-registrations', 'set-effective-registration.py', key_serializer,
                            value_serializer)

    key = name

    if unset:
        value = None
    else:
        alarm_class = None
        alarm_instance = get_instance()

        value = EffectiveRegistration(alarm_class, alarm_instance)

    producer.send(key, value)


cli()
