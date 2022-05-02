#!/usr/bin/env python3

"""
    Set alarm location.
"""

import click
from jaws_libp.clients import LocationProducer
from jaws_libp.entities import AlarmLocation


# pylint: disable=duplicate-code,missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is location name and value is JSON "
                   "with parent field")
@click.option('--unset', is_flag=True, help="Remove the location")
@click.argument('name')
@click.option('--parent', '-p', help="Name of parent Location or None if top-level Location")
def set_location(file, unset, name, parent) -> None:
    producer = LocationProducer('set_location.py')

    key = name

    if file:
        producer.import_records(name)
    else:
        if unset:
            value = None
        else:
            value = AlarmLocation(parent)

        producer.send(key, value)


def click_main() -> None:
    set_location()


if __name__ == "__main__":
    click_main()
