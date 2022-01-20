#!/usr/bin/env python3

import os
import click
import json

from confluent_kafka.serialization import StringSerializer

from jlab_jaws.avro.serde import AlarmInstanceSerde
from jlab_jaws.avro.entities import AlarmInstance, \
    SimpleProducer, EPICSProducer, CALCProducer
from jlab_jaws.eventsource.cached_table import LocationCachedTable, log_exception

from common import JAWSProducer, get_registry_client


def line_to_kv(line):
    tokens = line.split("=", 1)
    key = tokens[0]
    value_obj = tokens[1]
    value_dict = json.loads(value_obj)
    value = AlarmInstanceSerde.from_dict(value_dict)

    return key, value


schema_registry_client = get_registry_client()
bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
locations_table = LocationCachedTable(bootstrap_servers, schema_registry_client)
locations_table.start(log_exception)
locations = locations_table.await_get(5).keys()
locations_table.stop()


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON "
                   "encoded AVRO formatted per the alarm-instances-value schema")
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--alarmclass', help="The alarm class")
@click.option('--producersimple', is_flag=True, help="Simple alarm (producer)")
@click.option('--producerpv', help="The name of the EPICS CA PV that directly powers this alarm")
@click.option('--producerexpression', help="The CALC expression used to generate this alarm")
@click.option('--location', '-l', type=click.Choice(locations), multiple=True, help="The alarm location")
@click.option('--screencommand', help="The command to open the related control system screen")
@click.option('--maskedby', help="The optional parent alarm that masks this one")
@click.argument('name')
def cli(file, unset, alarmclass, producersimple, producerpv, producerexpression, location,
        screencommand, maskedby, name):
    key_serializer = StringSerializer()
    value_serializer = AlarmInstanceSerde.serializer(schema_registry_client)

    producer = JAWSProducer('alarm-instances', 'set-instance.py', key_serializer, value_serializer)

    key = name

    if file:
        producer.import_records(name, line_to_kv)
    else:
        if unset:
            value = None
        else:
            if producersimple is False and producerpv is None and producerexpression is None:
                raise click.ClickException(
                    "Must specify one of --producersimple, --producerpv, --producerexpression")

            if producersimple:
                p = SimpleProducer()
            elif producerpv:
                p = EPICSProducer(producerpv)
            else:
                p = CALCProducer(producerexpression)

            if alarmclass is None:
                alarmclass = "base"

            value = AlarmInstance(alarmclass,
                                  p,
                                  location,
                                  maskedby,
                                  screencommand)

        producer.send(key, value)


cli()
