#!/usr/bin/env python3

import os

import pwd
import types
import click
import json

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient

from jlab_jaws.avro.serde import AlarmRegistrationSerde
from jlab_jaws.avro.entities import AlarmRegistration, \
    SimpleProducer, EPICSProducer, CALCProducer
from jlab_jaws.avro.entities import AlarmLocation, AlarmCategory, AlarmPriority

from common import delivery_report

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

registrations_value_serializer = AlarmRegistrationSerde.serializer(schema_registry_client)

locations = AlarmLocation._member_names_
categories = AlarmCategory._member_names_
priorities = AlarmPriority._member_names_

registrations_producer_conf = {'bootstrap.servers': bootstrap_servers,
                               'key.serializer': StringSerializer('utf_8'),
                               'value.serializer': registrations_value_serializer}
alarm_producer = SerializingProducer(registrations_producer_conf)

registrations_topic = 'alarm-registrations'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name), ('producer', 'set-registration.py'), ('host', os.uname().nodename)]


def send(producer, topic):
    producer.produce(topic=topic, value=params.value, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


def registrations_import(file):
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

        alarm_producer.produce(topic=registrations_topic, value=value_obj, key=key, headers=hdrs)

    alarm_producer.flush()


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON encoded AVRO formatted per the alarm-registrations-value schema")
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--alarmclass', help="The alarm class")
@click.option('--producersimple', is_flag=True, help="Simple alarm (producer)")
@click.option('--producerpv', help="The name of the EPICS CA PV that directly powers this alarm")
@click.option('--producerexpression', help="The CALC expression used to generate this alarm")
@click.option('--location', type=click.Choice(locations), help="The alarm location")
@click.option('--category', type=click.Choice(categories), help="The alarm category")
@click.option('--priority', type=click.Choice(priorities), help="The alarm priority")
@click.option('--filterable/--not-filterable', is_flag=True, default=None,
              help="True if alarm can be filtered out of view; inherits from class if None")
@click.option('--latching/--not-latching', is_flag=True, default=None,
              help="Indicate that the alarm latches and requires acknowledgement to clear; inherits from class if None")
@click.option('--screenpath', help="The path the alarm screen display")
@click.option('--pointofcontactusername', help="The point of contact user name")
@click.option('--rationale', help="The alarm rationale")
@click.option('--correctiveaction', help="The corrective action")
@click.option('--maskedby', help="The optional parent alarm that masks this one")
@click.option('--ondelayseconds', type=int, default=None, help="Number of on delay seconds")
@click.option('--offdelayseconds', type=int, default=None, help="Number of off delay seconds")
@click.argument('name')
def cli(file, unset, alarmclass, producersimple, producerpv, producerexpression, location, category,
        priority, filterable, latching, screenpath, pointofcontactusername, rationale,
        correctiveaction, maskedby, ondelayseconds, offdelayseconds, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if file:
        registrations_import(name)
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

        send(alarm_producer, registrations_topic)


cli()
