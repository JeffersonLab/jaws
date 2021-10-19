#!/usr/bin/env python3

import os
import pwd
import types
import click
import time

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.entities import EffectiveAlarm, AlarmState, AlarmOverrideSet, \
    OverriddenAlarmType, EffectiveRegistration, EffectiveActivation, \
    DisabledOverride, FilteredOverride, LatchedOverride, MaskedOverride, OnDelayedOverride, OffDelayedOverride, \
    ShelvedOverride, ShelvedReason, AlarmRegistration, AlarmLocation, AlarmCategory, AlarmPriority, SimpleProducer
from jlab_jaws.avro.serde import EffectiveAlarmSerde

from common import delivery_report

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = StringSerializer()
value_serializer = EffectiveAlarmSerde.serializer(schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'effective-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name), ('producer', 'set-effective-alarms.py'),
        ('host', os.uname().nodename)]


def send():
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


def get_overrides(override):
    overrides = AlarmOverrideSet(None, None, None, None, None, None, None)

    timestamp_seconds = time.time() + 5;
    timestamp_millis = int(timestamp_seconds * 1000);

    if override == "Shelved":
        overrides.shelved = ShelvedOverride(timestamp_millis, None, ShelvedReason.Other, False)
    elif override == "OnDelayed":
        overrides.on_delayed = OnDelayedOverride(timestamp_millis)
    elif override == "OffDelayed":
        overrides.off_delayed = OffDelayedOverride(timestamp_millis)
    elif override == "Disabled":
        overrides.disabled = DisabledOverride(None)
    elif override == "Filtered":
        overrides.filtered = FilteredOverride("testing")
    elif override == "Masked":
        overrides.masked = MaskedOverride()
    else:  # assume Latched
        overrides.latched = LatchedOverride()

    return overrides


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
@click.option('--state', required=True, type=click.Choice(AlarmState._member_names_), help="The state")
@click.option('--override', type=click.Choice(OverriddenAlarmType._member_names_), help="The state")
@click.argument('name')
def cli(unset, state, override, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if unset:
        params.value = None
    else:
        overrides = get_overrides(override)
        actual_reg = get_effective_registration()
        calculated_reg = get_effective_registration()

        registration = EffectiveRegistration(None, actual_reg, calculated_reg)
        activation = EffectiveActivation(None, overrides, AlarmState[state])

        params.value = EffectiveAlarm(registration, activation)

    send()


cli()
