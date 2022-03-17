#!/usr/bin/env python3

"""
    Lists the effective registrations.
"""

import click

from jaws_libp.clients import EffectiveRegistrationConsumer, CategoryConsumer


class ClassAndCategoryFilter:
    def __init__(self, category, alarm_class):
        self._category = category
        self._alarm_class = alarm_class

    def filter_if(self, key, value):
        return (self._category is None or (value is not None and self._category == value.category)) and \
               (self._alarm_class is None or (value is not None and self._alarm_class == value.alarm_class))


categories = []


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice(categories),
              help="Only show registrations in the specified category (Options queried on-demand from "
                   "alarm-categories topic)")
@click.option('--alarm_class', help="Only show registrations in the specified class")
def list_effective_registrations(monitor, nometa, export, category, alarm_class) -> None:
    consumer = EffectiveRegistrationConsumer('list_effective_registrations.py')

    filter_obj = ClassAndCategoryFilter(category, alarm_class)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    global categories

    cat_consumer = CategoryConsumer('list_effective_registrations.py')
    categories = cat_consumer.get_keys_then_done()
    list_effective_registrations()


if __name__ == "__main__":
    click_main()

