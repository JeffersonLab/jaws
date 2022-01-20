#!/usr/bin/env python3

import click
import time

from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.entities import EffectiveAlarm, AlarmState, AlarmOverrideSet, \
    OverriddenAlarmType, EffectiveRegistration, EffectiveActivation, \
    DisabledOverride, FilteredOverride, LatchedOverride, MaskedOverride, OnDelayedOverride, OffDelayedOverride, \
    ShelvedOverride, ShelvedReason, SimpleProducer, AlarmInstance
from jlab_jaws.avro.serde import EffectiveAlarmSerde

from common import JAWSProducer, get_registry_client


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


def get_instance():
    return AlarmInstance("base",
                         SimpleProducer(),
                         ["INJ"],
                         "alarm1",
                         "command1")


@click.command()
@click.option('--unset', is_flag=True, help="present to clear state, missing to set state")
@click.option('--state', required=True, type=click.Choice(AlarmState._member_names_), help="The state")
@click.option('--override', type=click.Choice(OverriddenAlarmType._member_names_), help="The state")
@click.argument('name')
def cli(unset, state, override, name):
    schema_registry_client = get_registry_client()

    key_serializer = StringSerializer()
    value_serializer = EffectiveAlarmSerde.serializer(schema_registry_client)

    producer = JAWSProducer('effective-alarms', 'set-effective-alarm.py', key_serializer, value_serializer)

    key = name

    if unset:
        value = None
    else:
        overrides = get_overrides(override)
        alarm_instance= get_instance()

        registration = EffectiveRegistration(None, alarm_instance)
        activation = EffectiveActivation(None, overrides, AlarmState[state])

        value = EffectiveAlarm(registration, activation)

    producer.send(key, value)


cli()
