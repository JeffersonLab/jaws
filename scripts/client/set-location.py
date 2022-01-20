#!/usr/bin/env python3

import click
import json

from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.entities import AlarmLocation
from jlab_jaws.avro.serde import AlarmLocationSerde

from common import JAWSProducer, get_registry_client


def line_to_kv(line):
    tokens = line.split("=", 1)
    key = tokens[0]
    value_obj = tokens[1]
    value_dict = json.loads(value_obj)
    value = AlarmLocationSerde.from_dict(value_dict)
    return key, value


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is location name and value is JSON "
                   "with parent field")
@click.option('--unset', is_flag=True, help="Remove the location")
@click.argument('name')
@click.option('--parent', '-p', help="Name of parent Location or None if top-level Location")
def cli(file, unset, name, parent):
    schema_registry_client = get_registry_client()

    key_serializer = StringSerializer()
    value_serializer = AlarmLocationSerde.serializer(schema_registry_client)

    producer = JAWSProducer('alarm-locations', 'set-location.py', key_serializer, value_serializer)

    key = name

    if file:
        producer.import_records(name, line_to_kv)
    else:
        if unset:
            value = None
        else:
            value = AlarmLocation(parent)

        producer.send(key, value)


cli()
