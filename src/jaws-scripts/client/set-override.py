#!/usr/bin/env python3

import click
import time

from jlab_jaws.entities import AlarmOverrideUnion, LatchedOverride, FilteredOverride, MaskedOverride, \
    DisabledOverride, OnDelayedOverride, OffDelayedOverride, ShelvedOverride, AlarmOverrideKey, OverriddenAlarmType, \
    ShelvedReason
from jlab_jaws.clients import OverrideProducer


@click.command()
@click.option('--override', type=click.Choice(OverriddenAlarmType._member_names_), help="The type of override")
@click.option('--unset', is_flag=True, help="Remove the override")
@click.option('--expirationseconds', type=int, help="The number of seconds until the shelved status expires, None for "
                                                    "indefinite")
@click.option('--reason', type=click.Choice(ShelvedReason._member_names_), help="The explanation for why this alarm "
                                                                                "has been shelved")
@click.option('--oneshot', is_flag=True, help="Whether shelving is one-shot or continuous")
@click.option('--comments', help="Operator explanation for why suppressed")
@click.option('--filtername', help="Name of filter rule associated with this override")
@click.argument('name')
def cli(override, unset, expirationseconds, reason, oneshot, comments, filtername, name):
    producer = OverrideProducer('set-override.py')

    if override is None:
        raise click.ClickException("--override is required")

    key = AlarmOverrideKey(name, OverriddenAlarmType[override])

    if expirationseconds is not None:
        timestamp_seconds = time.time() + expirationseconds
        timestamp_millis = int(timestamp_seconds * 1000)

    if unset:
        value = None
    else:
        if override == "Shelved":
            if reason is None:
                raise click.ClickException("--reason is required")

            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = ShelvedOverride(timestamp_millis, comments, ShelvedReason[reason], oneshot)

        elif override == "OnDelayed":
            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = OnDelayedOverride(timestamp_millis)
        elif override == "OffDelayed":
            if expirationseconds is None:
                raise click.ClickException("--expirationseconds is required")

            msg = OffDelayedOverride(timestamp_millis)
        elif override == "Disabled":
            msg = DisabledOverride(comments)
        elif override == "Filtered":
            if filtername is None:
                raise click.ClickException("--filtername is required")

            msg = FilteredOverride(filtername)
        elif override == "Masked":
            msg = MaskedOverride()
        else: # assume Latched
            msg = LatchedOverride()

        value = AlarmOverrideUnion(msg)

    producer.send(key, value)


cli()

