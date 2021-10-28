#!/usr/bin/env python3

import os

import pwd
import types
import click
import json

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient

from jlab_jaws.avro.serde import AlarmRegistrationSerde, AlarmClassSerde
from jlab_jaws.avro.entities import AlarmRegistration, AlarmClass, \
    SimpleProducer, EPICSProducer, CALCProducer
from jlab_jaws.avro.entities import AlarmLocation, AlarmCategory, AlarmPriority

from common import delivery_report

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

alarm_value_serializer = AlarmRegistrationSerde.serializer(schema_registry_client)
class_value_serializer = AlarmClassSerde.serializer(schema_registry_client)

locations = AlarmLocation._member_names_
categories = AlarmCategory._member_names_
priorities = AlarmPriority._member_names_

alarm_producer_conf = {'bootstrap.servers': bootstrap_servers,
                       'key.serializer': StringSerializer('utf_8'),
                       'value.serializer': alarm_value_serializer}
alarm_producer = SerializingProducer(alarm_producer_conf)

class_producer_conf = {'bootstrap.servers': bootstrap_servers,
                       'key.serializer': StringSerializer('utf_8'),
                       'value.serializer': class_value_serializer}
class_producer = SerializingProducer(class_producer_conf)

alarm_topic = 'alarm-registrations'
class_topic = 'alarm-classes'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name), ('producer', 'set-classified.py'), ('host', os.uname().nodename)]


def send(producer, topic):
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


def alarms_import(file):
    print("Loading file", file)
    handle = open(file, 'r')
    lines = handle.readlines()

    for line in lines:
        tokens = line.split("=", 1)
        key = tokens[0]
        value = tokens[1]
        v = json.loads(value)
        print("{}={}".format(key, v))

        value_obj = AlarmRegistrationSerde.from_dict(v)

        alarm_producer.produce(topic=alarm_topic, value=value_obj, key=key, headers=hdrs)

    alarm_producer.flush()


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

        print('Message: {}={}'.format(key_obj, value_obj))

        class_producer.produce(topic=class_topic, value=value_obj, key=key_obj, headers=hdrs)

    class_producer.flush()


@click.command()
@click.option('--editclass', is_flag=True,
              help='Edit class definition instead of alarm definition (edit class defaults)')
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON encoded AVRO formatted per the registered-alarms-value schema")
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--alarmclass', help="The alarm class")
@click.option('--producersimple', is_flag=True, help="Simple alarm (producer)")
@click.option('--producerpv', help="The name of the EPICS CA PV that directly powers this alarm")
@click.option('--producerexpression', help="The CALC expression used to generate this alarm")
@click.option('--location', type=click.Choice(locations), help="The alarm location")
@click.option('--category', type=click.Choice(categories), help="The alarm category")
@click.option('--priority', type=click.Choice(priorities), help="The alarm priority")
@click.option('--filterable', is_flag=True, default=None, help="True if alarm can be filtered out of view")
@click.option('--latching', is_flag=True, default=None,
              help="Indicate that the alarm latches and requires acknowledgement to clear")
@click.option('--screenpath', help="The path the alarm screen display")
@click.option('--pointofcontactusername', help="The point of contact user name")
@click.option('--rationale', help="The alarm rationale")
@click.option('--correctiveaction', help="The corrective action")
@click.option('--maskedby', help="The optional parent alarm that masks this one")
@click.option('--ondelayseconds', type=int, default=None, help="Number of on delay seconds")
@click.option('--offdelayseconds', type=int, default=None, help="Number of off delay seconds")
@click.argument('name')
def cli(editclass, file, unset, alarmclass, producersimple, producerpv, producerexpression, location, category,
        priority, filterable, latching, screenpath, pointofcontactusername, rationale,
        correctiveaction, maskedby, ondelayseconds, offdelayseconds, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if editclass:
        if file:
            classes_import(name)
        else:
            if unset:
                params.value = None
            else:
                if location is None:
                    raise click.ClickException("--location required")

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

                if screenpath is None:
                    raise click.ClickException("--screenpath required")

                # TODO: filterable and latching should be required in registered-class-value schema
                if filterable is None:
                    filterable = True

                if latching is None:
                    latching = True

                # TODO: None not allowed right now for both delay ints...
                if ondelayseconds is None:
                    ondelayseconds = 0

                if offdelayseconds is None:
                    offdelayseconds = 0

                params.value = AlarmClass(AlarmLocation[location],
                                               AlarmCategory[category],
                                               AlarmPriority[priority],
                                               rationale,
                                               correctiveaction,
                                               pointofcontactusername,
                                               latching,
                                               filterable,
                                               ondelayseconds,
                                               offdelayseconds,
                                               maskedby,
                                               screenpath)

            send(class_producer, class_topic)
    else:
        if file:
            alarms_import(name)
        else:
            if unset:
                params.value = None
            else:
                if producersimple is False and producerpv is None and producerexpression is None:
                    raise click.ClickException(
                        "Must specify one of --producersimple, --producerpv, --producerexpression")

                if producersimple:
                    p = SimpleProducer()
                elif producerpv:
                    p = EPICSProducer(producerpv)
                else:
                    p = CALCProducer(producerexpression)

                if alarmclass is None:
                    alarmclass = "base"

                params.value = AlarmRegistration(AlarmLocation[location] if location is not None else None,
                                               AlarmCategory[category] if category is not None else None,
                                               AlarmPriority[priority] if priority is not None else None,
                                               rationale, correctiveaction,
                                               pointofcontactusername, latching, filterable,
                                               ondelayseconds, offdelayseconds, maskedby, screenpath,
                                               alarmclass, p)

            send(alarm_producer, alarm_topic)


cli()
