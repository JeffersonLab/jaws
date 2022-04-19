#!/usr/bin/env python3

"""
    Set effective alarm.

    **Note**: This is generally for testing only and should be done automatically via
    `jaws-effective-processor <https://github.com/JeffersonLab/jaws-effective-processor>`_
"""

import time

import click
from jaws_libp.clients import EffectiveAlarmProducer
from jaws_libp.entities import EffectiveAlarm, AlarmState, AlarmOverrideSet, \
    OverriddenAlarmType, EffectiveRegistration, EffectiveActivation, \
    DisabledOverride, FilteredOverride, LatchedOverride, MaskedOverride, OnDelayedOverride, OffDelayedOverride, \
    ShelvedOverride, ShelvedReason, SimpleProducer, AlarmInstance


# pylint: disable=duplicate-code
def __get_overrides(override):
    overrides = AlarmOverrideSet(None, None, None, None, None, None, None)

    timestamp_seconds = time.time() + 5
    timestamp_millis = int(timestamp_seconds * 1000)

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
    else:  # assume Latched
        overrides.latched = LatchedOverride()

    return overrides


def __get_instance():
    return AlarmInstance("base",
                         SimpleProducer(),
                         ["INJ"],
                         "alarm1",
                         "command1")


# pylint: disable=duplicate-code,missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--unset', is_flag=True, help="present to clear state, missing to set state")
@click.option('--state', required=True, type=click.Choice(list(map(lambda c: c.name, AlarmState))), help="The state")
@click.option('--override', type=click.Choice(list(map(lambda c: c.name, OverriddenAlarmType))), help="The state")
@click.argument('name')
def set_effective_alarm(unset, state, override, name):
    producer = EffectiveAlarmProducer('set_effective_alarm.py')

    key = name

    if unset:
        value = None
    else:
        overrides = __get_overrides(override)
        alarm_instance = __get_instance()

        registration = EffectiveRegistration(None, alarm_instance)
        activation = EffectiveActivation(None, overrides, AlarmState[state])

        value = EffectiveAlarm(registration, activation)

    producer.send(key, value)


def click_main() -> None:
    set_effective_alarm()


if __name__ == "__main__":
    click_main()
