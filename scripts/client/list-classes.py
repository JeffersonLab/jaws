#!/usr/bin/env python3

import click

from jlab_jaws.clients import ClassConsumer, CategoryConsumer


class CategoryFilter:
    def __init__(self, category):
        self._category = category

    def filter_if(self, key, value):
        return self._category is None or (value is not None and self._category == value.category)


cat_consumer = CategoryConsumer('list-classes.py')
categories = cat_consumer.get_keys_then_done()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice(categories), help="Only show registered alarms in the specified category")
def cli(monitor, nometa, export, category):
    consumer = ClassConsumer('list-classes.py')

    filter_obj = CategoryFilter(category)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


cli()
