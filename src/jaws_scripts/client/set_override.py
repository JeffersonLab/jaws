#!/usr/bin/env python3

"""
    Set alarm override.
"""

import time

import click
from jaws_libp.clients import OverrideProducer
from jaws_libp.entities import AlarmOverrideUnion, LatchedOverride, FilteredOverride, MaskedOverride, \
    DisabledOverride, OnDelayedOverride, OffDelayedOverride, ShelvedOverride, AlarmOverrideKey, OverriddenAlarmType, \
    ShelvedReason


# pylint: disable=missing-function-docstring,too-many-arguments,no-value-for-parameter,too-many-branches
@click.command()
@click.option('--override', type=click.Choice(list(map(lambda c: c.name, OverriddenAlarmType))),
              help="The type of override")
@click.option('--unset', is_flag=True, help="Remove the override")
@click.option('--expirationseconds', type=int, help="The number of seconds until the override status expires")
@click.option('--expirationts', type=int, help="UNIX timestamp (millis since epoch 1970) when the override status "
                                               "expires, Overridden by --expirationseconds "
                                               "(so only use one or the other)")
@click.option('--reason', type=click.Choice(list(map(lambda c: c.name, ShelvedReason))),
              help="The explanation for why this alarm has been shelved")
@click.option('--oneshot', is_flag=True, help="Whether shelving is one-shot or continuous")
@click.option('--comments', help="Operator explanation for why suppressed")
@click.option('--filtername', help="Name of filter rule associated with this override")
@click.argument('name')
def set_override(override, unset, expirationseconds, expirationts, reason, oneshot, comments, filtername, name) -> None:
    producer = OverrideProducer('set_override.py')

    if override is None:
        raise click.ClickException("--override is required")

    key = AlarmOverrideKey(name, OverriddenAlarmType[override])

    if expirationseconds is not None:
        timestamp_seconds = time.time() + expirationseconds
        expirationts = int(timestamp_seconds * 1000)

    if unset:
        value = None
    else:
        if override == "Shelved":
            if reason is None:
                raise click.ClickException("--reason is required")

            if expirationts is None:
                raise click.ClickException("--expirationseconds is required")

            msg = ShelvedOverride(expirationts, comments, ShelvedReason[reason], oneshot)

        elif override == "OnDelayed":
            if expirationts is None:
                raise click.ClickException("--expirationseconds is required")

            msg = OnDelayedOverride(expirationts)
        elif override == "OffDelayed":
            if expirationts is None:
                raise click.ClickException("--expirationseconds is required")

            msg = OffDelayedOverride(expirationts)
        elif override == "Disabled":
            msg = DisabledOverride(comments)
        elif override == "Filtered":
            if filtername is None:
                raise click.ClickException("--filtername is required")

            msg = FilteredOverride(filtername)
        elif override == "Masked":
            msg = MaskedOverride()
        else:  # assume Latched
            msg = LatchedOverride()

        value = AlarmOverrideUnion(msg)

    producer.send(key, value)


def click_main() -> None:
    set_override()


if __name__ == "__main__":
    click_main()
