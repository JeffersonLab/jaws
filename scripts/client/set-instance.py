#!/usr/bin/env python3

import click

from jlab_jaws.clients import LocationConsumer, InstanceProducer
from jlab_jaws.entities import AlarmInstance, \
    SimpleProducer, EPICSProducer, CALCProducer


consumer = LocationConsumer('set-instance.py')
locations = consumer.get_keys_then_done()


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
    producer = InstanceProducer('set-instance.py')

    key = name

    if file:
        producer.import_records(name)
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
