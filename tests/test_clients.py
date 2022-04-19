import os

import pytest
from jaws_libp.clients import InstanceConsumer, InstanceProducer
from jaws_libp.entities import AlarmInstance, SimpleProducer


@pytest.mark.usefixtures('deps_using_docker_compose')
def test_instance_client():

    producer = InstanceProducer('set_instance.py')

    producer.send("alarm1", AlarmInstance("base", SimpleProducer(), ["INJ"], None, None))

    consumer = InstanceConsumer('list_instances.py')

    #consumer.export_records()

    #captured = capsys.readouterr()

    #assert captured.out == '{"name": "alarm1"}\n'


