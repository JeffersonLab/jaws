#!/usr/bin/env python3

import click
from confluent_kafka import Message
from typing import List
from jlab_jaws.clients import CategoryConsumer


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
    consumer = CategoryConsumer('list-categories.py')

    head = ['Category']

    consumer.consume(monitor, nometa, export, head, msg_to_list)


cli()
