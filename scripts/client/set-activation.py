#!/usr/bin/env python3

import click

from jlab_jaws.clients import ActivationProducer
from jlab_jaws.entities import AlarmActivationUnion, SimpleAlarming, EPICSAlarming, NoteAlarming, EPICSSEVR, \
    EPICSSTAT


@click.command()
@click.option('--unset', is_flag=True, help="present to clear an alarm, missing to set active")
@click.option('--note', help="The note (only for NoteAlarming)")
@click.option('--sevr', type=click.Choice(EPICSSEVR._member_names_), help="The sevr (only for EPICSAlarming)")
@click.option('--stat', type=click.Choice(EPICSSTAT._member_names_), help="The stat (only for EPICSAlarming)")
@click.argument('name')
def cli(unset, note, stat, sevr, name):
    producer = ActivationProducer('set-activation.py')

    key = name

    if unset:
        value = None
    else:
        if sevr and stat:
            msg = EPICSAlarming(EPICSSEVR[sevr], EPICSSTAT[stat])
        elif note:
            msg = NoteAlarming(note)
        else:
            msg = SimpleAlarming()

        value = AlarmActivationUnion(msg)

    producer.send(key, value)


cli()
