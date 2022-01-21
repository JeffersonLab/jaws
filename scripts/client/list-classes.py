#!/usr/bin/env python3
from typing import List

import click
from confluent_kafka import Message

from confluent_kafka.serialization import StringDeserializer

from common import JAWSConsumer, StringSerde, ClassSerde, get_registry_client


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.category,
               value.priority.name if value.priority is not None else None,
               value.rationale.replace("\n", "\\n ") if value.rationale is not None else None,
               value.corrective_action.replace("\n", "\\n") if value.corrective_action is not None else None,
               value.point_of_contact_username,
               value.latching,
               value.filterable,
               value.on_delay_seconds,
               value.off_delay_seconds]

    return row


class CategoryFilter:
    def __init__(self, category):
        self._category = category

    def filter_if(self, key, value):
        return self._category is None or (value is not None and self._category == value.category)


cat_consumer = JAWSConsumer('alarm-categories', 'list-categories.py', StringSerde(), StringSerde())
categories = cat_consumer.get_records()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice(categories), help="Only show registered alarms in the specified category")
def cli(monitor, nometa, export, category):
    schema_registry_client = get_registry_client()

    consumer = JAWSConsumer('alarm-classes', 'list-classes.py', StringSerde(), ClassSerde(schema_registry_client))

    filter_obj = CategoryFilter(category)

    if monitor:
        consumer.print_records_continuous()
    elif export:
        consumer.export_records(filter_obj.filter_if)
    else:
        consumer.print_table(msg_to_list,
                             ["Class Name", "Category", "Priority", "Rationale", "Corrective Action",
                             "P.O.C. Username", "Latching", "Filterable", "On Delay", "Off Delay"],
                             nometa, filter_obj.filter_if)


cli()
