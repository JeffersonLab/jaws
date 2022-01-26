#!/usr/bin/env python3

import click
from jlab_jaws.clients import OverrideConsumer


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def cli(monitor, nometa, export):
    consumer = OverrideConsumer('list-overrides.py')

    consumer.consume_then_done(monitor, nometa, export)


cli()
