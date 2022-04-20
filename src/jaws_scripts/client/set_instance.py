#!/usr/bin/env python3

"""
    Set alarm registration instance.

    **Note**: bulk imports with ``--file`` expect alarm instance records formatted in
    `AVRO JSON Encoding <https://avro.apache.org/docs/current/spec.html#json_encoding>`_.
    See `Example file <https://github.com/JeffersonLab/jaws/blob/main/examples/data/instances>`_.
"""

import click

from jaws_libp.clients import LocationConsumer, InstanceProducer
from jaws_libp.entities import AlarmInstance, \
    SimpleProducer, EPICSProducer, CALCProducer

LOCATIONS = []

if __name__ == "__main__":
    consumer = LocationConsumer('set_instance.py')
    LOCATIONS = consumer.get_keys_then_done()


# pylint: disable=duplicate-code,missing-function-docstring,too-many-arguments,no-value-for-parameter
@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON "
                   "encoded AVRO formatted per the alarm-instances-value schema")
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--alarmclass', help="The alarm class")
@click.option('--producersimple', is_flag=True, help="Simple alarm (producer)")
@click.option('--producerpv', help="The name of the EPICS CA PV that directly powers this alarm")
@click.option('--producerexpression', help="The CALC expression used to generate this alarm")
@click.option('--location', '-l', type=click.Choice(LOCATIONS), multiple=True,
              help="The alarm location (Options queried on-demand from alarm-locations topic).  Multiple locations "
                   "allowed.")
@click.option('--screencommand', help="The command to open the related control system screen")
@click.option('--maskedby', help="The optional parent alarm that masks this one")
@click.argument('name')
def set_instance(file, unset, alarmclass, producersimple, producerpv, producerexpression, location,
                 screencommand, maskedby, name) -> None:
    producer = InstanceProducer('set_instance.py')

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
                source_producer = SimpleProducer()
            elif producerpv:
                source_producer = EPICSProducer(producerpv)
            else:
                source_producer = CALCProducer(producerexpression)

            if alarmclass is None:
                alarmclass = "base"

            value = AlarmInstance(alarmclass,
                                  source_producer,
                                  location,
                                  maskedby,
                                  screencommand)

        producer.send(key, value)


def click_main() -> None:
    set_instance()


if __name__ == "__main__":
    click_main()
