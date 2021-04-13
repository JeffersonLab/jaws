#!/usr/bin/env python3

import os
import pwd
import types
import click
import json

import avro.schema

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

with open(projectpath + '/config/subject-schemas/registered-alarms-value.avsc', 'r') as file:
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

avro_serializer = AvroSerializer(value_schema_str,
                                 schema_registry_client)

value_schema = avro.schema.Parse(value_schema_str)

groups = value_schema.fields[0].type.symbols
locations = value_schema.fields[2].type.schemas[1].symbols
categories = value_schema.fields[3].type.schemas[1].symbols
priorities = value_schema.fields[4].type.schemas[1].symbols

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': StringSerializer('utf_8'),
                 'value.serializer': avro_serializer}
producer = SerializingProducer(producer_conf)

topic = 'registered-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-registered.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = params.value

    producer.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()

def doImport(file) :
   print("Loading file", file)
   handle = open(file, 'r')
   lines = handle.readlines()

   for line in lines:
       tokens = line.split("=", 1)
       key = tokens[0]
       value = tokens[1]
       v = json.loads(value)
       print("{}={}".format(key, v))

       # Trying to work around union serialization issues: https://github.com/confluentinc/confluent-kafka-python/pull/785
       # Note that kafka-avro-console-consumer provided by Confluent requires proper JSON AVRO encoding https://avro.apache.org/docs/current/spec.html#json_encoding
       if 'org.jlab.alarms.EPICSProducer' in v['producer']:
           v['producer'] = v['producer']['org.jlab.alarms.EPICSProducer']
       elif 'org.jlab.alarms.StreamRuleProducer' in v['producer']:
           v['producer'] = v['producer']['org.jlab.alarms.StreamRuleProducer']
       else:
           v['producer'] = v['producer']['org.jlab.alarms.SimpleProducer']

       producer.produce(topic=topic, value=v, key=key, headers=hdrs)

   producer.flush()


@click.command()
@click.option('--file', is_flag=True, help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON encoded AVRO formatted per the registered-alarms-value schema")
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--group', type=click.Choice(groups), help="The alarm group")
@click.option('--producersimple', is_flag=True, help="Simple alarm (producer)")
@click.option('--producerpv', help="The name of the EPICS CA PV that directly powers this alarm")
@click.option('--producerexpression', help="The CALC expression used to generate this alarm")
@click.option('--location', type=click.Choice(locations), help="The alarm location")
@click.option('--category', type=click.Choice(categories), help="The alarm category")
@click.option('--priority', type=click.Choice(priorities), help="The alarm priority")
@click.option('--filterable', is_flag=True, default=None, help="True if alarm can be filtered out of view")
@click.option('--latching', is_flag=True, default=None, help="Indicate that the alarm latches and requires acknowledgement to clear")
@click.option('--screenpath', help="The path the alarm screen display")
@click.option('--pointofcontactusername', help="The point of contact user name")
@click.option('--rationale', help="The alarm rationale")
@click.option('--correctiveaction', help="The corrective action")
@click.option('--maskedby', help="The optional parent alarm that masks this one")
@click.argument('name')

def cli(file, unset, group, producersimple, producerpv, producerexpression, location, category, priority, filterable, latching, screenpath, pointofcontactusername, rationale, correctiveaction, maskedby, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if(file):
        doImport(name)
    else:
        if unset:
            params.value = None
        else:
            if producersimple == False and producerpv == None and producerexpression == None:
                raise click.ClickException("Must specify one of --producersimple, --producerpv, --producerexpression")

            if producersimple:
                producer = {}
            elif producerpv:
                producer = {"pv": producerpv}
            else:
                producer = {"expression" : producerexpression}

            params.value = {"group": group, "producer": producer, "location": location, "category": category, "priority": priority, "filterable": filterable, "latching": latching, "screenpath": screenpath, "pointofcontactusername": pointofcontactusername, "rationale": rationale, "correctiveaction": correctiveaction, "maskedby": maskedby}

            if group is None:
                params.value["group"] = "Default_Group"

            print('Message: {}'.format(params.value))

        send()

cli()

