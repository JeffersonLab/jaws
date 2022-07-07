#!/usr/bin/env python3

"""
    Lists the effective registrations.
"""

import click

from jaws_libp.console import EffectiveRegistrationConsoleConsumer


# pylint: disable=duplicate-code,disable=too-few-public-methods
class ClassFilter:
    """
        Filter class messages
    """
    def __init__(self, alarm_class):
        self._alarm_class = alarm_class

    # pylint: disable=unused-argument
    def filter_if(self, key, value):
        """
            Filter out messages unless the class natches the provided class
        """
        return self._alarm_class is None or (value is not None and self._alarm_class == value.alarm_class)


# pylint: disable=duplicate-code,missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--alarm_class', help="Only show registrations in the specified class")
def list_effective_registrations(monitor, nometa, export, alarm_class) -> None:
    consumer = EffectiveRegistrationConsoleConsumer('list_effective_registrations.py')

    filter_obj = ClassFilter(alarm_class)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    list_effective_registrations()


if __name__ == "__main__":
    click_main()
