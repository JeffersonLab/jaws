#!/usr/bin/env python3

"""
    Lists the alarm activations.
"""

import click
from jaws_libp.console import ActivationConsoleConsumer
from jaws_libp.entities import NoActivation


# pylint: disable=too-few-public-methods
class ActivationFilter:
    """
        Filter activation messages
    """
    def __init__(self, ignoreoff):
        self._ignoreoff = ignoreoff

    # pylint: disable=unused-argument
    def filter_if(self, key, value):
        """
            Filter out NoActivation messages if ignoreoff = True
        """
        return None if self._ignoreoff and isinstance(value.union, NoActivation) else value


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--ignoreoff', is_flag=True, help="Ignore NoActivation records")
def list_activations(monitor, nometa, export, ignoreoff) -> None:
    consumer = ActivationConsoleConsumer('list_activations.py')

    filter_obj = ActivationFilter(ignoreoff)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    list_activations()


if __name__ == "__main__":
    click_main()
