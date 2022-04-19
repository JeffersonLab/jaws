import os
import time

import pytest
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import wait_container_is_ready


@pytest.fixture
def deps_using_docker_compose():
    _compose = get_compose()
    time.sleep(10)
    yield _compose
    _compose.stop()


@wait_container_is_ready()
def get_compose():
    dirname = os.path.dirname(__file__)
    filepath = os.path.abspath(os.path.join(dirname, '..'))
    compose = DockerCompose(filepath, compose_file_name="deps.yml")
    compose.start()
    os.environ["BOOTSTRAP_SERVERS"] = "localhost:9094"
    os.environ["SCHEMA_REGISTRY"] = "http://localhost:8081"
    return compose
