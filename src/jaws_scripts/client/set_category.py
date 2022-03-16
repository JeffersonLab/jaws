#!/usr/bin/env python3

"""
    Set alarm category.
"""

import click

from jlab_jaws.clients import CategoryProducer


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is category name and value is "
                   "empty string")
@click.option('--unset', is_flag=True, help="Remove the category")
@click.argument('name')
def set_category(file, unset, name) -> None:
    producer = CategoryProducer('set_category.py')

    key = name

    if file:
        producer.import_records(name)
    else:
        if unset:
            value = None
        else:
            value = ""

        producer.send(key, value)


def click_main() -> None:
    set_category()


if __name__ == "__main__":
    click_main()

