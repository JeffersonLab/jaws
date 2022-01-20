#!/usr/bin/env python3
import click

from confluent_kafka.serialization import StringSerializer

from common import JAWSProducer


def line_to_kv(line):
    key = line.rstrip()
    value = ""

    return key, value


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is category name and value is "
                   "empty string")
@click.option('--unset', is_flag=True, help="Remove the category")
@click.argument('name')
def cli(file, unset, name):
    key_serializer = StringSerializer('utf_8')
    value_serializer = StringSerializer('utf_8')

    producer = JAWSProducer('alarm-categories', 'set-category.py', key_serializer, value_serializer)

    key = name

    if file:
        producer.import_records(name, line_to_kv)
    else:
        if unset:
            value = None
        else:
            value = ""

        producer.send(key, value)


cli()
