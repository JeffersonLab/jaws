import time

from click.testing import CliRunner
from jaws_libp.avro.serde import OverrideSerde, OverrideKeySerde
from jaws_libp.entities import AlarmOverrideUnion, LatchedOverride, AlarmOverrideKey, OverriddenAlarmType, \
    MaskedOverride, DisabledOverride, FilteredOverride, ShelvedOverride, ShelvedReason, OnDelayedOverride, \
    OffDelayedOverride
from jaws_scripts.client.list_overrides import list_overrides
from jaws_scripts.client.set_override import set_override


def test_latched_override():
    alarm_name = "alarm1"
    override_type = OverriddenAlarmType.Latched
    override_key = AlarmOverrideKey(alarm_name, override_type)
    override = AlarmOverrideUnion(LatchedOverride())

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_override, [alarm_name, '--override', override_type.name])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_overrides, ['--export'])
        assert result.exit_code == 0

        override_serde = OverrideSerde(None)
        key_serde = OverrideKeySerde(None)
        assert result.output == key_serde.to_json(override_key) + '=' + override_serde.to_json(override) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_override, [alarm_name, '--unset', '--override', override_type.name])
        assert result.exit_code == 0


def test_masked_override():
    alarm_name = "alarm1"
    override_type = OverriddenAlarmType.Masked
    override_key = AlarmOverrideKey(alarm_name, override_type)
    override = AlarmOverrideUnion(MaskedOverride())

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_override, [alarm_name, '--override', override_type.name])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_overrides, ['--export'])
        assert result.exit_code == 0

        override_serde = OverrideSerde(None)
        key_serde = OverrideKeySerde(None)
        assert result.output == key_serde.to_json(override_key) + '=' + override_serde.to_json(override) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_override, [alarm_name, '--unset', '--override', override_type.name])
        assert result.exit_code == 0


def test_disabled_override():
    alarm_name = "alarm1"
    comments = "Out of Service"
    override_type = OverriddenAlarmType.Disabled
    override_key = AlarmOverrideKey(alarm_name, override_type)
    override = AlarmOverrideUnion(DisabledOverride(comments))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_override, [alarm_name, '--override', override_type.name, '--comments', comments])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_overrides, ['--export'])
        assert result.exit_code == 0

        override_serde = OverrideSerde(None)
        key_serde = OverrideKeySerde(None)
        assert result.output == key_serde.to_json(override_key) + '=' + override_serde.to_json(override) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_override, [alarm_name, '--unset', '--override', override_type.name])
        assert result.exit_code == 0


def test_filtered_override():
    alarm_name = "alarm1"
    filter = "Area"
    override_type = OverriddenAlarmType.Filtered
    override_key = AlarmOverrideKey(alarm_name, override_type)
    override = AlarmOverrideUnion(FilteredOverride(filter))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_override, [alarm_name, '--override', override_type.name, '--filtername', filter])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_overrides, ['--export'])
        assert result.exit_code == 0

        override_serde = OverrideSerde(None)
        key_serde = OverrideKeySerde(None)
        assert result.output == key_serde.to_json(override_key) + '=' + override_serde.to_json(override) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_override, [alarm_name, '--unset', '--override', override_type.name])
        assert result.exit_code == 0


def test_continuous_shelved_override():
    alarm_name = "alarm1"
    expiration_seconds = 15
    expiration_ts = int(time.time() + expiration_seconds) * 1000
    reason = ShelvedReason.Stale_Alarm
    oneshot = False
    comments = "Just until I hear back from tech"
    override_type = OverriddenAlarmType.Shelved
    override_key = AlarmOverrideKey(alarm_name, override_type)
    override = AlarmOverrideUnion(ShelvedOverride(expiration_ts, comments, reason, oneshot))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_override, [alarm_name, '--override', override_type.name,
                                              '--expirationts', expiration_ts, '--comments', comments,
                                              '--reason', reason.name])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_overrides, ['--export'])
        assert result.exit_code == 0

        override_serde = OverrideSerde(None)
        key_serde = OverrideKeySerde(None)
        assert result.output == key_serde.to_json(override_key) + '=' + override_serde.to_json(override) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_override, [alarm_name, '--unset', '--override', override_type.name])
        assert result.exit_code == 0


def test_oneshot_shelved_override():
    alarm_name = "alarm1"
    expiration_seconds = 15
    expiration_ts = int(time.time() + expiration_seconds) * 1000
    reason = ShelvedReason.Stale_Alarm
    oneshot = True
    comments = "Just until I hear back from tech"
    override_type = OverriddenAlarmType.Shelved
    override_key = AlarmOverrideKey(alarm_name, override_type)
    override = AlarmOverrideUnion(ShelvedOverride(expiration_ts, comments, reason, oneshot))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_override, [alarm_name, '--override', override_type.name,
                                              '--expirationts', expiration_ts, '--comments', comments,
                                              '--reason', reason.name, '--oneshot'])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_overrides, ['--export'])
        assert result.exit_code == 0

        override_serde = OverrideSerde(None)
        key_serde = OverrideKeySerde(None)
        assert result.output == key_serde.to_json(override_key) + '=' + override_serde.to_json(override) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_override, [alarm_name, '--unset', '--override', override_type.name])
        assert result.exit_code == 0


def test_on_delayed_override():
    alarm_name = "alarm1"
    expiration_seconds = 15
    expiration_ts = int(time.time() + expiration_seconds) * 1000
    override_type = OverriddenAlarmType.OnDelayed
    override_key = AlarmOverrideKey(alarm_name, override_type)
    override = AlarmOverrideUnion(OnDelayedOverride(expiration_ts))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_override, [alarm_name, '--override', override_type.name,
                                              '--expirationts', expiration_ts])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_overrides, ['--export'])
        assert result.exit_code == 0

        override_serde = OverrideSerde(None)
        key_serde = OverrideKeySerde(None)
        assert result.output == key_serde.to_json(override_key) + '=' + override_serde.to_json(override) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_override, [alarm_name, '--unset', '--override', override_type.name])
        assert result.exit_code == 0


def test_off_delayed_override():
    alarm_name = "alarm1"
    expiration_seconds = 15
    expiration_ts = int(time.time() + expiration_seconds) * 1000
    override_type = OverriddenAlarmType.OffDelayed
    override_key = AlarmOverrideKey(alarm_name, override_type)
    override = AlarmOverrideUnion(OffDelayedOverride(expiration_ts))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_override, [alarm_name, '--override', override_type.name,
                                              '--expirationts', expiration_ts])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_overrides, ['--export'])
        assert result.exit_code == 0

        override_serde = OverrideSerde(None)
        key_serde = OverrideKeySerde(None)
        assert result.output == key_serde.to_json(override_key) + '=' + override_serde.to_json(override) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_override, [alarm_name, '--unset', '--override', override_type.name])
        assert result.exit_code == 0
