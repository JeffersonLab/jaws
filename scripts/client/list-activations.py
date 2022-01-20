#!/usr/bin/env python3

from typing import List

import click
from confluent_kafka import Message
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.avro.serde import AlarmActivationUnionSerde

from common import JAWSConsumer, get_registry_client


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value]

    return row


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def cli(monitor, nometa, export):
    schema_registry_client = get_registry_client()

    key_deserializer = StringDeserializer('utf_8')
    value_deserializer = AlarmActivationUnionSerde.deserializer(schema_registry_client)

    consumer = JAWSConsumer('alarm-activations', 'list-activations.py', key_deserializer, value_deserializer)

    if monitor:
        consumer.print_records_continuous()
    elif export:
        consumer.export_records(AlarmActivationUnionSerde)
    else:
        consumer.print_table(msg_to_list, ["Alarm Name", "Value"], nometa)


cli()
