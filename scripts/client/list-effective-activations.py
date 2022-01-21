#!/usr/bin/env python3

from typing import List

import click
from confluent_kafka import Message

from common import JAWSConsumer, get_registry_client, StringSerde, EffectiveActivationSerde


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
    schema_registry_client = get_registry_client()

    consumer = JAWSConsumer('effective-activations', 'list-effective-activations.py', StringSerde(),
                            EffectiveActivationSerde(schema_registry_client))

    if monitor:
        consumer.print_records_continuous()
    elif export:
        consumer.export_records()
    else:
        consumer.print_table(msg_to_list,
                             ["Alarm Name", "State", "Overrides"],
                             nometa)


cli()
