#!/usr/bin/env python3

import os

import pwd
import types
import click
import time

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.avro.entities import AlarmOverrideUnion, LatchedOverride, FilteredOverride, MaskedOverride, \
    DisabledOverride, OnDelayedOverride, OffDelayedOverride, ShelvedOverride, AlarmOverrideKey, OverriddenAlarmType, \
    ShelvedReason
from jlab_jaws.avro.serde import AlarmOverrideKeySerde, AlarmOverrideUnionSerde

from common import delivery_report, set_log_level_from_env

set_log_level_from_env()

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = AlarmOverrideKeySerde.serializer(schema_registry_client)
value_serializer = AlarmOverrideUnionSerde.serializer(schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'alarm-overrides'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-override.py'),('host',os.uname().nodename)]


def send():
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


@click.command()
@click.option('--override', type=click.Choice(OverriddenAlarmType._member_names_), help="The type of override")
@click.option('--unset', is_flag=True, help="Remove the override")
@click.option('--expirationseconds', type=int, help="The number of seconds until the shelved status expires, None for "
                                                    "indefinite")
@click.option('--reason', type=click.Choice(ShelvedReason._member_names_), help="The explanation for why this alarm "
                                                                                "has been shelved")
@click.option('--oneshot', is_flag=True, help="Whether shelving is one-shot or continuous")
@click.option('--comments', help="Operator explanation for why suppressed")
@click.option('--filtername', help="Name of filter rule associated with this override")
@click.argument('name')
def cli(override, unset, expirationseconds, reason, oneshot, comments, filtername, name):
    global params

    params = types.SimpleNamespace()

    if override is None:
        raise click.ClickException("--override is required")

    params.key = AlarmOverrideKey(name, OverriddenAlarmType[override])

    if expirationseconds is not None:
        timestamp_seconds = time.time() + expirationseconds;
        timestamp_millis = int(timestamp_seconds * 1000);

    if unset:
        params.value = None
    else:
        if override == "Shelved":
            if reason is None:
                raise click.ClickException("--reason is required")

            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = ShelvedOverride(timestamp_millis, comments, ShelvedReason[reason], oneshot)

        elif override == "OnDelayed":
            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = OnDelayedOverride(timestamp_millis)
        elif override == "OffDelayed":
            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = OffDelayedOverride(timestamp_millis)
        elif override == "Disabled":
            msg = DisabledOverride(comments)
        elif override == "Filtered":
            if filtername is None:
                raise click.ClickException("--filtername is required")

            msg = FilteredOverride(filtername)
        elif override == "Masked":
            msg = MaskedOverride()
        else: # assume Latched
            msg = LatchedOverride()

        params.value = AlarmOverrideUnion(msg)

    print(params.value)

    send()


cli()

