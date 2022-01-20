#!/usr/bin/env python3

import click

from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.entities import AlarmActivationUnion, SimpleAlarming, EPICSAlarming, NoteAlarming, EPICSSEVR, \
    EPICSSTAT
from jlab_jaws.avro.serde import AlarmActivationUnionSerde

from common import JAWSProducer, get_registry_client


@click.command()
@click.option('--unset', is_flag=True, help="present to clear an alarm, missing to set active")
@click.option('--note', help="The note (only for NoteAlarming)")
@click.option('--sevr', type=click.Choice(EPICSSEVR._member_names_), help="The sevr (only for EPICSAlarming)")
@click.option('--stat', type=click.Choice(EPICSSTAT._member_names_), help="The stat (only for EPICSAlarming)")
@click.argument('name')
def cli(unset, note, stat, sevr, name):
    schema_registry_client = get_registry_client()

    key_serializer = StringSerializer()
    value_serializer = AlarmActivationUnionSerde.serializer(schema_registry_client)

    producer = JAWSProducer('alarm-activations', 'set-activation.py', key_serializer, value_serializer)

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
