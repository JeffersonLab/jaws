#!/usr/bin/env python3

"""
    Set alarm activation.
"""

import click

from jaws_libp.clients import ActivationProducer
from jaws_libp.entities import AlarmActivationUnion, ChannelErrorActivation, Activation, EPICSActivation, \
    NoteActivation, NoActivation, EPICSSEVR, EPICSSTAT


# pylint: disable=missing-function-docstring,no-value-for-parameter,too-many-arguments
@click.command()
@click.option('--unset', is_flag=True, help="present to clear an alarm")
@click.option('--note', help="The note (only for NoteActivation)")
@click.option('--error', help="A channel error between JAWS and an alarm activation source such as Disconnected")
@click.option('--sevr', type=click.Choice(list(map(lambda c: c.name, EPICSSEVR))),
              help="The sevr (only for EPICSActivation)")
@click.option('--stat', type=click.Choice(list(map(lambda c: c.name, EPICSSTAT))),
              help="The stat (only for EPICSActivation)")
@click.argument('name')
def set_activation(unset, note, error, stat, sevr, name) -> None:
    producer = ActivationProducer('set_activation.py')

    key = name

    if unset:
        union = NoActivation()
    elif error:
        union = ChannelErrorActivation(error)
    elif sevr and stat:
        union = EPICSActivation(EPICSSEVR[sevr], EPICSSTAT[stat])
    elif note:
        union = NoteActivation(note)
    else:
        union = Activation()

    value = AlarmActivationUnion(union)

    producer.send(key, value)


def click_main() -> None:
    set_activation()


if __name__ == "__main__":
    click_main()
