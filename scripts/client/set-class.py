#!/usr/bin/env python3

import os

import pwd
import types
import click
import json

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient

from jlab_jaws.avro.serde import AlarmClassSerde
from jlab_jaws.avro.entities import AlarmClass
from jlab_jaws.avro.entities import AlarmPriority
from jlab_jaws.eventsource.cached_table import CategoryCachedTable, log_exception

from common import delivery_report, set_log_level_from_env

set_log_level_from_env()

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

class_value_serializer = AlarmClassSerde.serializer(schema_registry_client)

priorities = AlarmPriority._member_names_

class_producer_conf = {'bootstrap.servers': bootstrap_servers,
                       'key.serializer': StringSerializer('utf_8'),
                       'value.serializer': class_value_serializer}
class_producer = SerializingProducer(class_producer_conf)

class_topic = 'alarm-classes'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name), ('producer', 'set-class.py'), ('host', os.uname().nodename)]


def send(producer, topic):
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


def classes_import(file):
    print("Loading file", file)
    handle = open(file, 'r')
    lines = handle.readlines()

    for line in lines:
        tokens = line.split("=", 1)
        key = tokens[0]
        value = tokens[1]
        v = json.loads(value)
        print("{}={}".format(key, v))

        key_obj = key
        value_obj = AlarmClassSerde.from_dict(v)

        class_producer.produce(topic=class_topic, value=value_obj, key=key_obj, headers=hdrs,
                               on_delivery=delivery_report)

    class_producer.flush()


categories_table = CategoryCachedTable(bootstrap_servers)
categories_table.start(log_exception)
categories = categories_table.await_get(5).keys()
categories_table.stop()


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON "
                   "encoded AVRO formatted per the alarm-classes-value schema")
@click.option('--unset', is_flag=True, help="Remove the class")
@click.option('--category', type=click.Choice(categories), help="The alarm category")
@click.option('--priority', type=click.Choice(priorities), help="The alarm priority")
@click.option('--filterable/--not-filterable', is_flag=True, default=True,
              help="True if alarm can be filtered out of view")
@click.option('--latching/--not-latching', is_flag=True, default=True,
              help="Indicate that the alarm latches and requires acknowledgement to clear")
@click.option('--pointofcontactusername', help="The point of contact user name")
@click.option('--rationale', help="The alarm rationale")
@click.option('--correctiveaction', help="The corrective action")
@click.option('--ondelayseconds', type=int, default=None, help="Number of on delay seconds")
@click.option('--offdelayseconds', type=int, default=None, help="Number of off delay seconds")
@click.argument('name')
def cli(file, unset, category,
        priority, filterable, latching, pointofcontactusername, rationale,
        correctiveaction, ondelayseconds, offdelayseconds, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if file:
        classes_import(name)
    else:
        if unset:
            params.value = None
        else:
            if category is None:
                raise click.ClickException("--category required")

            if priority is None:
                raise click.ClickException("--priority required")

            if rationale is None:
                raise click.ClickException("--rationale required")

            if correctiveaction is None:
                raise click.ClickException("--correctiveaction required")

            if pointofcontactusername is None:
                raise click.ClickException("--pointofcontactusername required")

            params.value = AlarmClass(category,
                                      AlarmPriority[priority],
                                      rationale,
                                      correctiveaction,
                                      pointofcontactusername,
                                      latching,
                                      filterable,
                                      ondelayseconds,
                                      offdelayseconds)

        send(class_producer, class_topic)


cli()
