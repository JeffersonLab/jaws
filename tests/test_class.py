import os

from click.testing import CliRunner
from jaws_libp.entities import AlarmClass, AlarmPriority
from jaws_scripts.client.list_classes import list_classes
from jaws_scripts.client.set_class import set_class


def test_class():
    category = 'EXAMPLE_CATEGORY'
    class_name = "TESTING_CLASS"
    alarm_class = AlarmClass(category, AlarmPriority.P3_MINOR, 'TESTING_RATIONALE',
                             'TESTING_CORRECTIVE_ACTION', 'TESTING_POC', True, True, None, None)

    runner = CliRunner()

    # Set
    # result = runner.invoke(set_class, [class_name,
    #                                   '--category', alarm_class.category,
    #                                   '--priority', alarm_class.priority.name,
    #                                   '--rationale', alarm_class.rationale,
    #                                   '--correctiveaction', alarm_class.corrective_action,
    #                                   '--pointofcontactusername', alarm_class.point_of_contact_username])
    #print(result.output)
    #assert result.exit_code == 0

    # Get
    result = runner.invoke(list_classes, ['--export'])
    assert result.exit_code == 0
    #assert result.output == class_name + '={"parent": null}\n'
