#!/usr/bin/env python3

import click
from confluent_kafka import Message
from jlab_jaws.clients import EffectiveActivationConsumer
from typing import List


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.state.name]

    return row


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def cli(monitor, nometa, export):
    consumer = EffectiveActivationConsumer('list-effective-activations.py')

    head = ["Alarm Name", "State", "Overrides"]

    consumer.consume(monitor, nometa, export, head, msg_to_list)


cli()
