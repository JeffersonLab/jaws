#!/usr/bin/env python3

import click

from confluent_kafka import Message
from typing import List

from jlab_jaws.avro.clients import EffectiveRegistrationConsumer, CategoryConsumer


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.instance,
               value.alarm_class]

    return row


class ClassAndCategoryFilter:
    def __init__(self, category, alarm_class):
        self._category = category
        self._alarm_class = alarm_class

    def filter_if(self, key, value):
        return (self._category is None or (value is not None and self._category == value.category)) and \
               (self._alarm_class is None or (value is not None and self._alarm_class == value.alarm_class))


cat_consumer = CategoryConsumer('list-effective-registrations.py')
categories = cat_consumer.get_records()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice(categories), help="Only show registrations in the specified category")
@click.option('--alarm_class', help="Only show registrations in the specified class")
def cli(monitor, nometa, export, category, alarm_class):
    consumer = EffectiveRegistrationConsumer('list-effective-registrations.py')

    filter_obj = ClassAndCategoryFilter(category, alarm_class)

    head = ["Alarm Name", "Instance", "Class"],

    consumer.consume(monitor, nometa, export, head, msg_to_list, filter_obj.filter_if)


cli()
