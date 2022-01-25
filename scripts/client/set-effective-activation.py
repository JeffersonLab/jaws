#!/usr/bin/env python3

import click
import time

from jlab_jaws.clients import EffectiveActivationProducer
from jlab_jaws.entities import AlarmState, AlarmOverrideSet, \
    OverriddenAlarmType, EffectiveActivation, \
    DisabledOverride, FilteredOverride, LatchedOverride, MaskedOverride, OnDelayedOverride, OffDelayedOverride, \
    ShelvedOverride, ShelvedReason


def get_overrides(override):
    overrides = AlarmOverrideSet(None, None, None, None, None, None, None)

    timestamp_seconds = time.time() + 5;
    timestamp_millis = int(timestamp_seconds * 1000);

    if override == "Shelved":
        overrides.shelved = ShelvedOverride(timestamp_millis, None, ShelvedReason.Other, False)
    elif override == "OnDelayed":
        overrides.on_delayed = OnDelayedOverride(timestamp_millis)
    elif override == "OffDelayed":
        overrides.off_delayed = OffDelayedOverride(timestamp_millis)
    elif override == "Disabled":
        overrides.disabled = DisabledOverride(None)
    elif override == "Filtered":
        overrides.filtered = FilteredOverride("testing")
    elif override == "Masked":
        overrides.masked = MaskedOverride()
    elif override == "Latched":
        overrides.latched = LatchedOverride()

    return overrides


@click.command()
@click.option('--unset', is_flag=True, help="present to clear state, missing to set state")
@click.option('--state', required=True, type=click.Choice(AlarmState._member_names_), help="The state")
@click.option('--override', type=click.Choice(OverriddenAlarmType._member_names_), help="The state")
@click.argument('name')
def cli(unset, state, override, name):
    producer = EffectiveActivationProducer('set-effective-activation.py')

    key = name

    if unset:
        value = None
    else:
        overrides = get_overrides(override)

        value = EffectiveActivation(None, overrides, AlarmState[state])

    producer.send(key, value)


cli()
