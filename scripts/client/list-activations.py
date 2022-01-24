#!/usr/bin/env python3

import click
from confluent_kafka import Message
from jlab_jaws.avro.clients import ActivationConsumer
from typing import List


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
    consumer = ActivationConsumer('list-activations.py')

    head = ["Alarm Name", "Value"]

    consumer.consume(monitor, nometa, export, head, msg_to_list)


cli()
