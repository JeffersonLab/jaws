#!/usr/bin/env python3

"""
    Set effective notification.

    **Note**: This is generally for testing only and should be done automatically via
    `jaws-effective-processor <https://github.com/JeffersonLab/jaws-effective-processor>`_
"""

import time

import click
from jaws_libp.clients import EffectiveNotificationProducer
from jaws_libp.entities import AlarmState, AlarmOverrideSet, \
    OverriddenAlarmType, EffectiveNotification, \
    DisabledOverride, FilteredOverride, LatchedOverride, MaskedOverride, OnDelayedOverride, OffDelayedOverride, \
    ShelvedOverride, ShelvedReason


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
    elif override == "Latched":
        overrides.latched = LatchedOverride()

    return overrides


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--unset', is_flag=True, help="Remove the effective notification")
@click.option('--state', type=click.Choice(list(map(lambda c: c.name, AlarmState))), help="The state")
@click.option('--override', type=click.Choice(list(map(lambda c: c.name, OverriddenAlarmType))), help="The override")
@click.argument('name')
def set_effective_notification(unset, state, override, name) -> None:
    producer = EffectiveNotificationProducer('set_effective_notification.py')

    key = name

    if unset:
        value = None
    else:
        overrides = __get_overrides(override)

        if state is None:
            state = "Normal"

        value = EffectiveNotification(None, overrides, AlarmState[state])

    producer.send(key, value)


def click_main() -> None:
    set_effective_notification()


if __name__ == "__main__":
    click_main()
