#!/usr/bin/env python3
from typing import List

import click

from confluent_kafka import Message

from common import get_registry_client, StringSerde, JAWSConsumer, LocationSerde


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.parent]

    return row


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def cli(monitor, nometa, export):
    schema_registry_client = get_registry_client()

    consumer = JAWSConsumer('alarm-locations', 'list-locations.py', StringSerde(),
                            LocationSerde(schema_registry_client))

    if monitor:
        consumer.print_records_continuous()
    elif export:
        consumer.export_records()
    else:
        consumer.print_table(msg_to_list, ["Location", "Parent"], nometa)


cli()
