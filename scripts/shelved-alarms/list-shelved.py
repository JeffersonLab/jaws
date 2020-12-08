#!/usr/bin/env python3

import os
import types
import click
import time

from confluent_kafka import avro, Consumer
from confluent_kafka.avro import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer as AvroSerde
from confluent_kafka.avro.serializer import SerializerError
from confluent_kafka import OFFSET_BEGINNING


bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry = CachedSchemaRegistryClient(conf)

avro_serde = AvroSerde(schema_registry)

empty = False

def my_on_assign(consumer, partitions):
    # We are assuming one partition, otherwise low/high would each be array and checking against high water mark would probably not work since other partitions could still contain unread messages.
    global low
    global high
    global empty
    for p in partitions:
        p.offset = OFFSET_BEGINNING
        low, high = consumer.get_watermark_offsets(p)
        if high == 0:
            empty = True
    consumer.assign(partitions)

def disp_msg(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key().decode('utf-8')
    value = avro_serde.decode_message(msg.value())

    if value != None and value['expiration'] != None:
        value['expiration'] = time.ctime(value['expiration'] / 1000)

    ts = time.ctime(timestamp[1] / 1000)

    user = ''
    producer = ''
    host = ''

    if headers is not None:
        lookup = dict(headers)
        bytez = lookup.get('user', b'')
        user = bytez.decode()
        bytez = lookup.get('producer', b'')
        producer = bytez.decode()
        bytez = lookup.get('host', b'')
        host = bytez.decode()

    print(ts, '|', user, '|', producer, '|', host, '|', key, value)

def list():
    ts = time.time()

    c = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': 'list-shelved.py' + str(ts)})

    c.subscribe(['shelved-alarms'], on_assign=my_on_assign)

    while True:
        try:
            msg = c.poll(1.0)

        except SerializerError as e:
            print("Message deserialization failed for {}: {}".format(msg, e))
            break

        if (not params.monitor) and empty:
            break

        if msg is None:
            continue

        if msg.error():
            print("AvroConsumer error: {}".format(msg.error()))
            continue

        disp_msg(msg)

        if (not params.monitor) and msg.offset() + 1 == high:
            break

    c.close()

@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")

def cli(monitor):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor

    list()

cli()
