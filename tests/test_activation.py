from click.testing import CliRunner
from jaws_libp.avro.serde import ActivationSerde
from jaws_libp.entities import AlarmActivationUnion, Activation, ChannelErrorActivation, NoteActivation, \
    EPICSActivation, EPICSSTAT, EPICSSEVR
from jaws_scripts.client.list_activations import list_activations
from jaws_scripts.client.set_activation import set_activation


def test_activation():
    alarm_name = "alarm1"
    activation = AlarmActivationUnion(Activation())

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_activation, [alarm_name])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_activations, ['--export', '--ignoreoff'])
        assert result.exit_code == 0

        activation_serde = ActivationSerde(None)
        assert result.output == alarm_name + '=' + activation_serde.to_json(activation) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_activation, [alarm_name, '--unset'])
        assert result.exit_code == 0


def test_note_activation():
    alarm_name = "alarm2"
    note = "TESTING"
    activation = AlarmActivationUnion(NoteActivation(note))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_activation, [alarm_name, '--note', note])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_activations, ['--export', '--ignoreoff'])
        assert result.exit_code == 0

        activation_serde = ActivationSerde(None)
        assert result.output == alarm_name + '=' + activation_serde.to_json(activation) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_activation, [alarm_name, '--unset'])
        assert result.exit_code == 0


def test_epics_activation():
    alarm_name = "alarm3"
    sevr = EPICSSEVR.MINOR
    stat = EPICSSTAT.HIHI
    activation = AlarmActivationUnion(EPICSActivation(sevr, stat))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_activation, [alarm_name, '--sevr', sevr.name, '--stat', stat.name])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_activations, ['--export', '--ignoreoff'])
        assert result.exit_code == 0

        activation_serde = ActivationSerde(None)
        assert result.output == alarm_name + '=' + activation_serde.to_json(activation) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_activation, [alarm_name, '--unset'])
        assert result.exit_code == 0


def test_error_activation():
    alarm_name = "alarm4"
    error = "Never Connected"
    activation = AlarmActivationUnion(ChannelErrorActivation(error))

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_activation, [alarm_name, '--error', error])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_activations, ['--export', '--ignoreoff'])
        assert result.exit_code == 0

        activation_serde = ActivationSerde(None)
        assert result.output == alarm_name + '=' + activation_serde.to_json(activation) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_activation, [alarm_name, '--unset'])
        assert result.exit_code == 0
