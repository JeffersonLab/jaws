#!/usr/bin/env python3

import click

from jlab_jaws.entities import AlarmLocation
from jlab_jaws.clients import LocationProducer


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is location name and value is JSON "
                   "with parent field")
@click.option('--unset', is_flag=True, help="Remove the location")
@click.argument('name')
@click.option('--parent', '-p', help="Name of parent Location or None if top-level Location")
def cli(file, unset, name, parent):
    producer = LocationProducer('set-location.py')

    key = name

    if file:
        producer.import_records(name)
    else:
        if unset:
            value = None
        else:
            value = AlarmLocation(parent)

        producer.send(key, value)


cli()
