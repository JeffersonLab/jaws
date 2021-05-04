#!/usr/bin/env python3

import os

import pwd
import types
import click
import time

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.avro.subject_schemas.entities import OverriddenAlarmValue, LatchedAlarm, FilteredAlarm, MaskedAlarm, \
    DisabledAlarm, OnDelayedAlarm, OffDelayedAlarm, ShelvedAlarm, OverriddenAlarmKey, OverriddenAlarmType, \
    ShelvedAlarmReason
from jlab_jaws.avro.subject_schemas.serde import OverriddenAlarmKeySerde, OverriddenAlarmValueSerde


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered')


bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = OverriddenAlarmKeySerde.serializer(schema_registry_client)
value_serializer = OverriddenAlarmValueSerde.serializer(schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'overridden-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-overridden.py'),('host',os.uname().nodename)]

def send() :
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


@click.command()
@click.option('--override', type=click.Choice(OverriddenAlarmType._member_names_), help="The type of override")
@click.option('--unset', is_flag=True, help="Remove the override")
@click.option('--expirationseconds', type=int, help="The number of seconds until the shelved status expires, None for indefinite")
@click.option('--reason', type=click.Choice(ShelvedAlarmReason._member_names_), help="The explanation for why this alarm has been shelved")
@click.option('--oneshot', is_flag=True, help="Whether shelving is one-shot or continuous")
@click.option('--comments', help="Operator explanation for why suppressed")
@click.option('--filtername', help="Name of filter rule associated with this override")
@click.argument('name')

def cli(override, unset, expirationseconds, reason, oneshot, comments, filtername, name):
    global params

    params = types.SimpleNamespace()

    if override == None:
        raise click.ClickException("--override is required")

    params.key = OverriddenAlarmKey(name, OverriddenAlarmType[override])

    if expirationseconds != None:
        timestampSeconds = time.time() + expirationseconds;
        timestampMillis = int(timestampSeconds * 1000);

    if unset:
        params.value = None
    else:
        if override == "Shelved":
            if reason is None:
                raise click.ClickException("--reason is required")

            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = ShelvedAlarm(timestampMillis, comments, reason, oneshot)

        elif override == "OnDelayed":
            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = OnDelayedAlarm(timestampMillis)
        elif override == "OffDelayed":
            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = OffDelayedAlarm(timestampMillis)
        elif override == "Disabled":
            msg = DisabledAlarm(comments)
        elif override == "Filtered":
            if filtername is None:
                raise click.ClickException("--filtername is required")

            msg = FilteredAlarm(filtername)
        elif override == "Masked":
            msg = MaskedAlarm()
        else: # assume Latched
            msg = LatchedAlarm()

        params.value = OverriddenAlarmValue(msg)

    print(params.value)

    send()

cli()

