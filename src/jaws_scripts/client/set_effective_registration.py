#!/usr/bin/env python3

"""
    Set effective registration.

    **Note**: This is generally for testing only and should be done automatically via
    `jaws-effective-processor <https://github.com/JeffersonLab/jaws-effective-processor>`_
"""

import click
from jaws_libp.clients import EffectiveRegistrationProducer
from jaws_libp.entities import EffectiveRegistration, \
    AlarmInstance, SimpleProducer


# pylint: disable=duplicate-code
def __get_instance():
    return AlarmInstance("base",
                         SimpleProducer(),
                         ["INJ"],
                         "alarm1",
                         "command1")


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--unset', is_flag=True, help="present to clear state, missing to set state")
@click.argument('name')
def set_effective_registration(unset, name):
    producer = EffectiveRegistrationProducer('set_effective_registration.py')

    key = name

    if unset:
        value = None
    else:
        alarm_class = None
        alarm_instance = __get_instance()

        value = EffectiveRegistration(alarm_class, alarm_instance)

    producer.send(key, value)


def click_main() -> None:
    set_effective_registration()


if __name__ == "__main__":
    click_main()
