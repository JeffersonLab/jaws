import pytest

from jaws_scripts.broker.create_topics import create_topics
from jaws_scripts.broker.delete_topics import delete_topics


@pytest.fixture(scope="session", autouse=True)
def reset_topics():
    # We want to start testing with empty topics
    try:
        delete_topics()
    except:
        pass

    try:
        create_topics()
    except:
        print("Unable to create topics")
