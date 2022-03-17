#!/usr/bin/env python3

"""
    Lists the alarm activations.
"""

import click
from jaws_libp.clients import ActivationConsumer


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def list_activations(monitor, nometa, export) -> None:
    consumer = ActivationConsumer('list_activations.py')

    consumer.consume_then_done(monitor, nometa, export)


def click_main() -> None:
    list_activations()


if __name__ == "__main__":
    click_main()

