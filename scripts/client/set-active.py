#!/usr/bin/env python3

import os
import pwd
import types
import click

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer
from jlab_jaws.avro.subject_schemas.entities import ActiveAlarm, SimpleAlarming, EPICSAlarming, NoteAlarming, EPICSSEVR, \
    EPICSSTAT
from jlab_jaws.avro.subject_schemas.serde import ActiveAlarmSerde


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
value_serializer = ActiveAlarmSerde.serializer(schema_registry_client)

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': key_serializer,
                 'value.serializer': value_serializer}
producer = SerializingProducer(producer_conf)

topic = 'active-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-active.py'),('host',os.uname().nodename)]


def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = params.value

    producer.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()


@click.command()
@click.option('--unset', is_flag=True, help="present to clear an alarm, missing to set active")
@click.option('--note', help="The note (only for NoteAlarming)")
@click.option('--sevr', type=click.Choice(EPICSSEVR._member_names_), help="The sevr (only for EPICSAlarming)")
@click.option('--stat', type=click.Choice(EPICSSTAT._member_names_), help="The stat (only for EPICSAlarming)")
@click.argument('name')
def cli(unset, note, stat, sevr, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if unset:
      params.value = None
    else:
        if sevr and stat:
            msg = EPICSAlarming(sevr, stat)
        elif note:
            msg = NoteAlarming(note)
        else:
            msg = SimpleAlarming()

        params.value = ActiveAlarm(msg)

    send()


cli()
