#!/usr/bin/env python3

import click

from jlab_jaws.clients import EffectiveRegistrationConsumer, CategoryConsumer


class ClassAndCategoryFilter:
    def __init__(self, category, alarm_class):
        self._category = category
        self._alarm_class = alarm_class

    def filter_if(self, key, value):
        return (self._category is None or (value is not None and self._category == value.category)) and \
               (self._alarm_class is None or (value is not None and self._alarm_class == value.alarm_class))


cat_consumer = CategoryConsumer('list-effective-registrations.py')
categories = cat_consumer.get_keys_then_done()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice(categories), help="Only show registrations in the specified category")
@click.option('--alarm_class', help="Only show registrations in the specified class")
def cli(monitor, nometa, export, category, alarm_class):
    consumer = EffectiveRegistrationConsumer('list-effective-registrations.py')

    filter_obj = ClassAndCategoryFilter(category, alarm_class)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


cli()
