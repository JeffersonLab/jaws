#!/usr/bin/env python3

"""
    Lists the alarm registration instances.
"""

import click

from jaws_libp.clients import InstanceConsumer


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
def list_instances(monitor, nometa, export, alarm_class) -> None:
    consumer = InstanceConsumer('list_instances.py')

    filter_obj = ClassFilter(alarm_class)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    list_instances()


if __name__ == "__main__":
    click_main()

