#!/usr/bin/env python3

import os
import pwd
import types
import click

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../../'

with open(projectpath + '/config/subject-schemas/active-alarms-value.avsc', 'r') as file:
    value_schema_str = file.read()

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered')

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

key_serializer = StringSerializer()

value_serializer = AvroSerializer(value_schema_str,
                                  schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'active-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-active-epics.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = params.value

    producer.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()

@click.command()
@click.option('--sevr', type=click.Choice(['NO_ALARM', 'MINOR', 'MAJOR', 'INVALID']), help="The alarm severity as a priority for operators")
@click.option('--stat', type=click.Choice(["NO_ALARM","READ","WRITE","HIHI","HIGH","LOLO","LOW","STATE","COS","COMM","TIMEOUT","HW_LIMIT","CALC","SCAN","LINK","SOFT","BAD_SUB","UDF","DISABLE","SIMM","READ_ACCESS","WRITE_ACCESS"]), help="The alarm status")
@click.argument('name')

def cli(sevr, stat, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if sevr == None:
        raise click.ClickException(
            "Must specify option --sevr")

    if stat == None:
        stat = "NO_ALARM"

    params.value = {"msg": {"sevr": sevr, "stat": stat}}

    send()

cli()

