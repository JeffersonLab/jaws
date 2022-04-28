import os

from click import Choice
from click.testing import CliRunner
from jaws_libp.avro.serde import ClassSerde
from jaws_libp.entities import AlarmClass, AlarmPriority
from jaws_scripts.client.list_classes import list_classes
from jaws_scripts.client.set_class import set_class


def test_class():
    category = 'EXAMPLE_CATEGORY'
    class_name = "TESTING_CLASS"
    alarm_class = AlarmClass(category, AlarmPriority.P3_MINOR, 'TESTING_RATIONALE',
                             'TESTING_CORRECTIVE_ACTION', 'TESTING_POC', True, True, None, None)

    runner = CliRunner()

    set_class.params[2].type = Choice([category])

    # Set
    result = runner.invoke(set_class, [class_name,
                                       '--category', alarm_class.category,
                                       '--priority', alarm_class.priority.name,
                                       '--rationale', alarm_class.rationale,
                                       '--correctiveaction', alarm_class.corrective_action,
                                       '--pointofcontactusername', alarm_class.point_of_contact_username])
    assert result.exit_code == 0

    # Get
    result = runner.invoke(list_classes, ['--export'])
    assert result.exit_code == 0

    class_serde = ClassSerde(None)
    assert result.output == class_name + '=' + class_serde.to_json(alarm_class) + '\n'
