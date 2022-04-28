from click.testing import CliRunner
from jaws_libp.avro.serde import EffectiveActivationSerde
from jaws_libp.entities import AlarmState, EffectiveActivation, AlarmOverrideSet
from jaws_scripts.client.list_effective_activations import list_effective_activations
from jaws_scripts.client.set_effective_activation import set_effective_activation


def test_simple_effective_activation():
    alarm_name = "alarm1"
    activation = None
    overrides = AlarmOverrideSet(None, None, None, None, None, None, None)
    state = AlarmState.Active
    effective = EffectiveActivation(activation, overrides, state)

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_effective_activation, [alarm_name, '--state', state.name])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_effective_activations, ['--export'])
        assert result.exit_code == 0

        activation_serde = EffectiveActivationSerde(None)
        assert result.output == alarm_name + '=' + activation_serde.to_json(effective) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_effective_activation, [alarm_name, '--unset'])
        assert result.exit_code == 0

