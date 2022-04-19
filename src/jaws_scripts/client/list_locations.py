#!/usr/bin/env python3

"""
    Lists the alarm locations.

    **Note**: bulk imports with ``--file`` expect alarm class records formatted in
    `AVRO JSON Encoding <https://avro.apache.org/docs/current/spec.html#json_encoding>`_
    See `Example file <https://github.com/JeffersonLab/jaws/blob/main/examples/data/locations>`_.
"""

import click

from jaws_libp.clients import LocationConsumer


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def list_locations(monitor, nometa, export) -> None:
    consumer = LocationConsumer('list_locations.py')

    consumer.consume_then_done(monitor, nometa, export)


def click_main() -> None:
    list_locations()


if __name__ == "__main__":
    click_main()
