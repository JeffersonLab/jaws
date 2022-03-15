#!/usr/bin/env python3

import click

from jlab_jaws.entities import EffectiveRegistration, \
    AlarmInstance, SimpleProducer
from jlab_jaws.clients import EffectiveRegistrationProducer


def get_instance():
    return AlarmInstance("base",
                         SimpleProducer(),
                         ["INJ"],
                         "alarm1",
                         "command1")


@click.command()
@click.option('--unset', is_flag=True, help="present to clear state, missing to set state")
@click.argument('name')
def cli(unset, name):
    producer = EffectiveRegistrationProducer('set-effective-registration.py')

    key = name

    if unset:
        value = None
    else:
        alarm_class = None
        alarm_instance = get_instance()

        value = EffectiveRegistration(alarm_class, alarm_instance)

    producer.send(key, value)


cli()
