#!/usr/bin/env python3

"""
    Set alarm category.

    **Note**: bulk imports with ``--file`` expect alarm class records formatted in
    `AVRO JSON Encoding <https://avro.apache.org/docs/current/spec.html#json_encoding>`_
    See `Example file <https://github.com/JeffersonLab/jaws/blob/main/examples/data/categories>`_.
"""

import click

from jaws_libp.clients import CategoryProducer


# pylint: disable=missing-function-docstring,no-value-for-parameter
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
