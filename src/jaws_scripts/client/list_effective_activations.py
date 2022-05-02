#!/usr/bin/env python3

"""
    Lists the alarm effective activations.
"""

import click
from jaws_libp.clients import EffectiveActivationConsumer


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def list_effective_activations(monitor, nometa, export) -> None:
    consumer = EffectiveActivationConsumer('list_effective_activations.py')

    consumer.consume_then_done(monitor, nometa, export)


def click_main() -> None:
    list_effective_activations()


if __name__ == "__main__":
    click_main()
