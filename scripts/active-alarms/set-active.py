#!/usr/bin/env python3

import os
import pwd
import types
import click

# We can't use AvroProducer since it doesn't support string keys, see: https://github.com/confluentinc/confluent-kafka-python/issues/428
from confluent_kafka import avro, Producer
from confluent_kafka.avro import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer as AvroSerde
from avro.schema import Field

key_schema_str = """
{
    "type"      : "record",
    "name"      : "ActiveAlarmKey",
    "namespace" : "org.jlab.kafka.alarms",
    "doc"       : "Active alarms state (alarming or acknowledgment)",
    fields      : [
        {
            "name" : "alarmname",
            "type" : "string",
            "doc"  : "The unique name of the alarm"
        },
        {
            "name" : "msgtype",
            "type" : {
                "type"      : "enum",
                "name"      : "ActiveMessageType",
                "namespace" : "org.jlab.kafka.alarms",
                "doc"       : "Enumeration of possible message types",
                "symbols"   : ["alarming","acknowledgement"]
                
            },
            "doc"  : "The type of message included in the value - required as part of the key to ensure compaction keeps the latest message of each type" 
        }
    ]
}
"""

value_schema_str = """
{
   "type"      : "record",
   "name"      : "ActiveAlarmValue",   
   "namespace" : "org.jlab.kafka.alarms",
   "doc"       : "Alarming and Acknowledgements state",
   "fields"    : [
        {
            "name" : "ActiveState",
            "type" : [
                {
                    "type"      : "record",
                    "name"      : "AlarmingMsg",
                    "namespace" : "org.jlab.kafka.alarms",
                    "doc"       : "Alarming state for a basic alarm",
                    "fields"    : [
                        {
                           "name" : "alarming",
                           "type" : "boolean",
                           "doc"  : "true if the alarm is alarming, false otherwise"
                        }
                    ]
                },
                {
                    "type"      : "record",
                    "name"      : "AcknowledgementMsg",
                    "namespace" : "org.jlab.kafka.alarms",
                    "doc"       : "A basic acknowledgment message",
                    "fields"    : [
                        {
                            "name" : "acknowledged",
                            "type" : "boolean",
                            "doc"  : "true if the alarm is acknowledged, false otherwise"
                        }
                    ]
                },
                {
                    "type"      : "record",
                    "name"      : "EPICSAlarmingMsg",
                    "namespace" : "org.jlab.kafka.alarms",
                    "doc"       : "EPICS alarming state",
                    "fields"    : [
                        {
                            "name" : "state",
                            "type"    : {
                                "type"      : "enum",       
                                "name"      : "EPICSAlarmingEnum",
                                "namespace" : "org.jlab.kafka.alarms",
                                "doc"       : "Enumeration of possible EPICS alarming states",
                                "symbols"   : ["MAJOR","MINOR","NO_ALARM"]
                            },
                            "doc" : "Alarming state"
                        }
                    ]
                },
                {
                    "type"      : "record",
                    "name"      : "EPICSAcknowledgementMsg",
                    "namespace" : "org.jlab.kafka.alarms",
                    "doc"       : "EPICS acknowledgement state",
                    "fields"    : [
                        {
                            "name"    : "state",
                            "type"    : {
                                "type"      : "enum",
                                "name"      : "EPICSAcknowledgementEnum",
                                "namespace" : "org.jlab.kafka.alarms",
                                "doc"       : "Enumeration of possible EPICS acknowledgement states",
                                "symbols"   : ["MAJOR_ACK", "MINOR_ACK", "NO_ACK"]
                            },
                            "doc"     : "Indicates whether this alarm has been explicitly acknowledged - useful for latching alarms which can only be cleared after acknowledgement"        
                        }
                    ]
                }
            ],
            "doc" : "Two types of messages are allowed: Alarming and Acknowledgement; There can be multiple flavors of each type for different alarm producers; modeled as a nested union to avoid complications of union at root of schema."
        }
  ]
}
"""

value_schema = avro.loads(value_schema_str)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered')

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry = CachedSchemaRegistryClient(conf)

avro_serde = AvroSerde(schema_registry)
serialize_avro = avro_serde.encode_record_with_schema

p = Producer({
    'bootstrap.servers': bootstrap_servers,
    'on_delivery': delivery_report})

topic = 'active-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-active.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = serialize_avro(topic, value_schema, params.value, is_key=False)

    p.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs)
    p.flush()

@click.command()
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--priority', type=click.Choice(['P1_LIFE', 'P2_PROPERTY', 'P3_PRODUCTIVITY', 'P4_DIAGNOSTIC']), help="The alarm serverity as a priority for operators")
@click.option('--ack', is_flag=True, help="Acknowledge the alarm")
@click.argument('name')

def cli(unset, priority, ack, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if unset:
        params.value = None
    else:
        if priority == None:
            raise click.ClickException(
                    "Must specify option --priority")

        params.value = {"priority": priority, "acknowledged": ack}

    send()

cli()

