#!/usr/bin/env python3

import click

from typing import List
from confluent_kafka import Message
from jlab_jaws.clients import InstanceConsumer


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.alarm_class,
               value.producer,
               value.location,
               value.masked_by,
               value.screen_command]

    return row


class ClassFilter:
    def __init__(self, alarm_class):
        self._alarm_class = alarm_class

    def filter_if(self, key, value):
        return self._alarm_class is None or (value is not None and self._alarm_class == value.alarm_class)


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--alarm_class', help="Only show instances in the specified class")
def cli(monitor, nometa, export, alarm_class):
    consumer = InstanceConsumer('list-instances.py')

    filter_obj = ClassFilter(alarm_class)

    head = ["Alarm Name", "Class", "Producer", "Location", "Masked By", "Screen Command"]

    consumer.consume(monitor, nometa, export, head, msg_to_list, filter_obj.filter_if)


cli()
