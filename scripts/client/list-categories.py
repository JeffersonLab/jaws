#!/usr/bin/env python3

from typing import List

import click

from confluent_kafka.cimpl import Message
from confluent_kafka.serialization import StringDeserializer

from common import JAWSConsumer


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is not None:
        row = [key]
    else:
        row = [None]

    return row


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def cli(monitor, nometa, export):
    key_deserializer = StringDeserializer('utf_8')
    value_deserializer = StringDeserializer('utf_8')

    consumer = JAWSConsumer('alarm-categories', 'list-categories.py', key_deserializer, value_deserializer)

    if monitor:
        consumer.print_records_continuous()
    elif export:
        consumer.export_records()
    else:
        consumer.print_table(msg_to_list, ['Category'], nometa)


cli()
