from click.testing import CliRunner
from jaws_libp.avro.serde import EffectiveNotificationSerde
from jaws_libp.entities import AlarmState, EffectiveNotification, AlarmOverrideSet
from jaws_scripts.client.list_effective_notifications import list_effective_notifications
from jaws_scripts.client.set_effective_notification import set_effective_notification


def test_simple_effective_notification():
    alarm_name = "alarm1"
    activation = None
    overrides = AlarmOverrideSet(None, None, None, None, None, None, None)
    state = AlarmState.Active
    effective = EffectiveNotification(activation, overrides, state)

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_effective_notification, [alarm_name, '--state', state.name])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_effective_notifications, ['--export'])
        assert result.exit_code == 0

        activation_serde = EffectiveNotificationSerde(None)
        assert result.output == alarm_name + '=' + activation_serde.to_json(effective) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_effective_notification, [alarm_name, '--unset'])
        assert result.exit_code == 0

