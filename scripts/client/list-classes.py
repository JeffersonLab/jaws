#!/usr/bin/env python3

import click

from confluent_kafka import Message
from jlab_jaws.clients import ClassConsumer, CategoryConsumer
from typing import List


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


cat_consumer = CategoryConsumer('list-classes.py')
categories = cat_consumer.get_records()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice(categories), help="Only show registered alarms in the specified category")
def cli(monitor, nometa, export, category):
    consumer = ClassConsumer('list-classes.py')

    filter_obj = CategoryFilter(category)

    head = ["Class Name", "Category", "Priority", "Rationale", "Corrective Action",
            "P.O.C. Username", "Latching", "Filterable", "On Delay", "Off Delay"],

    consumer.consume(monitor, nometa, export, head, msg_to_list, filter_obj.filter_if)


cli()
