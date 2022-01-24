#!/usr/bin/env python3

from typing import List

import click
from confluent_kafka import Message
from jlab_jaws.avro.clients import OverrideConsumer


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
    consumer = OverrideConsumer('list-overrides.py')

    head = ["Alarm Name", "Override Type", "Value"]

    consumer.consume(monitor, nometa, export, head, msg_to_list)


cli()
