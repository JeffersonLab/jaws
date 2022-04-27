from click.testing import CliRunner
from jaws_scripts.client.list_locations import list_locations
from jaws_scripts.client.set_location import set_location


def test_location():
    location = 'EXAMPLE_LOCATION'

    runner = CliRunner()

    # Set
    result = runner.invoke(set_location, [location])
    assert result.exit_code == 0

    # Get
    result = runner.invoke(list_locations, ['--export'])
    assert result.exit_code == 0
    assert result.output == location + '={"parent": null}\n'
