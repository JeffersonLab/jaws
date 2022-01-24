#!/usr/bin/env python3

import os
import click
from confluent_kafka import Message
from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.avro.clients import EffectiveAlarmConsumer
from typing import List

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)


def msg_to_list(msg: Message) -> List[str]:
    key = msg.key()
    value = msg.value()

    if value is None:
        row = [key, None]
    else:
        row = [key,
               value.activation.state.name,
               value.activation.overrides,
               value.registration.instance]

    return row


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def cli(monitor, nometa, export):
    consumer = EffectiveAlarmConsumer('list-effective-alarms.py')

    head = ["Alarm Name", "State", "Overrides", "Instance"]

    consumer.consume(monitor, nometa, export, head, msg_to_list)


cli()
