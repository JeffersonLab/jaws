from click.testing import CliRunner
from jaws_scripts.client.list_categories import list_categories
from jaws_scripts.client.set_category import set_category


def test_category():
    category = 'EXAMPLE_CATEGORY'

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_category, [category])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_categories, ['--export'])
        assert result.exit_code == 0
        assert result.output == category + '=\n'

    finally:
        # Clear
        result = runner.invoke(set_category, [category, '--unset'])
        assert result.exit_code == 0
