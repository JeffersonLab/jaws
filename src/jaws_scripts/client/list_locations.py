#!/usr/bin/env python3

import click

from jlab_jaws.clients import LocationConsumer


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def main(monitor, nometa, export):
    consumer = LocationConsumer('list_locations.py')

    consumer.consume_then_done(monitor, nometa, export)


if __name__ == "__main__":
    main()

