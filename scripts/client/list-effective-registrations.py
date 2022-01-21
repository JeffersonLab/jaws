#!/usr/bin/env python3

import click

from confluent_kafka import Message
from common import get_registry_client, JAWSConsumer, StringSerde, EffectiveRegistrationSerde
from typing import List


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


cat_consumer = JAWSConsumer('alarm-categories', 'list-categories.py', StringSerde(), StringSerde())
categories = cat_consumer.get_records()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice(categories), help="Only show registrations in the specified category")
@click.option('--alarm_class', help="Only show registrations in the specified class")
def cli(monitor, nometa, export, category, alarm_class):
    schema_registry_client = get_registry_client()

    consumer = JAWSConsumer('effective-registrations', 'list-effective-registrations.py', StringSerde(),
                            EffectiveRegistrationSerde(schema_registry_client))

    filter_obj = ClassAndCategoryFilter(category, alarm_class)

    if monitor:
        consumer.print_records_continuous()
    elif export:
        consumer.export_records(filter_obj.filter_if)
    else:
        consumer.print_table(msg_to_list,
                             ["Alarm Name", "Instance", "Class"],
                             nometa,
                             filter_obj.filter_if)


cli()
