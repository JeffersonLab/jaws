#!/usr/bin/env python3

"""
    Set alarm activation.
"""

import click

from jaws_libp.clients import ActivationProducer
from jaws_libp.entities import AlarmActivationUnion, ChannelError, SimpleAlarming, EPICSAlarming, NoteAlarming, \
    EPICSSEVR, EPICSSTAT


# pylint: disable=missing-function-docstring,no-value-for-parameter,too-many-arguments
@click.command()
@click.option('--unset', is_flag=True, help="present to clear an alarm, missing to set active")
@click.option('--note', help="The note (only for NoteAlarming)")
@click.option('--error', help="A channel error between JAWS and an alarm activation source such as Disconnected")
@click.option('--sevr', type=click.Choice(list(map(lambda c: c.name, EPICSSEVR))),
              help="The sevr (only for EPICSAlarming)")
@click.option('--stat', type=click.Choice(list(map(lambda c: c.name, EPICSSTAT))),
              help="The stat (only for EPICSAlarming)")
@click.argument('name')
def set_activation(unset, note, error, stat, sevr, name) -> None:
    producer = ActivationProducer('set_activation.py')

    key = name

    if unset:
        value = None
    else:
        if error:
            msg = ChannelError(error)
        elif sevr and stat:
            msg = EPICSAlarming(EPICSSEVR[sevr], EPICSSTAT[stat])
        elif note:
            msg = NoteAlarming(note)
        else:
            msg = SimpleAlarming()

        value = AlarmActivationUnion(msg)

    producer.send(key, value)


def click_main() -> None:
    set_activation()


if __name__ == "__main__":
    click_main()
