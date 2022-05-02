#!/usr/bin/env python3

"""
    Lists the alarm registration classes.

    **Note**: With the ``--export`` option you can export a file that can be imported by ``set-class --file``.
"""

import click

from jaws_libp.clients import ClassConsumer, CategoryConsumer


# pylint: disable=too-few-public-methods
class CategoryFilter:
    """
        Filter category messages
    """
    def __init__(self, category):
        self._category = category

    # pylint: disable=unused-argument
    def filter_if(self, key, value):
        """
            Filter out messages unless the category matches the provided category
        """
        return self._category is None or (value is not None and self._category == value.category)


CATEGORIES = []

if __name__ == "__main__":
    cat_consumer = CategoryConsumer('list_classes.py')
    CATEGORIES = cat_consumer.get_keys_then_done()


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice(CATEGORIES),
              help="Only show registered alarms in the specified category (Options queried on-demand from "
                   "alarm-categories topic)")
def list_classes(monitor, nometa, export, category) -> None:
    consumer = ClassConsumer('list_classes.py')

    filter_obj = CategoryFilter(category)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    list_classes()


if __name__ == "__main__":
    click_main()
