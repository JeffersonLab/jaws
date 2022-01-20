#!/usr/bin/env python3

from typing import List

import click
from confluent_kafka import Message
from jlab_jaws.avro.serde import AlarmOverrideKeySerde, AlarmOverrideUnionSerde

from common import JAWSConsumer, get_registry_client


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key.name,
               key.type,
               None]
    else:
        row = [key.name,
               key.type.name,
               value]

    return row


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def cli(monitor, nometa, export):
    schema_registry_client = get_registry_client()

    key_deserializer = AlarmOverrideKeySerde.deserializer(schema_registry_client)
    value_deserializer = AlarmOverrideUnionSerde.deserializer(schema_registry_client)

    consumer = JAWSConsumer('alarm-overrides', 'list-overrides.py', key_deserializer, value_deserializer)

    if monitor:
        consumer.print_records_continuous()
    elif export:
        consumer.export_records(AlarmOverrideUnionSerde)
    else:
        consumer.print_table(msg_to_list, ["Alarm Name", "Override Type", "Value"], nometa)


cli()
