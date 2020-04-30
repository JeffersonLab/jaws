#!/usr/bin/env python3

import os

from confluent_kafka import avro, Consumer
from confluent_kafka.avro import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer as AvroSerde
from confluent_kafka.avro.serializer import SerializerError
from confluent_kafka import OFFSET_BEGINNING


bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
schema_registry = CachedSchemaRegistryClient(os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081'))

avro_serde = AvroSerde(schema_registry)

c = Consumer({
    'bootstrap.servers': bootstrap_servers,
    'group.id': 'list-active.sh'})

def my_on_assign(consumer, partitions):
    # We are assuming one partition, otherwise low/high would each be array and checking against high water mark would probably not work since other partitions could still contain unread messages.
    global low
    global high
    for p in partitions:
        p.offset = OFFSET_BEGINNING
        low, high = c.get_watermark_offsets(p)
    consumer.assign(partitions)

c.subscribe(['active-alarms'], on_assign=my_on_assign)

while True:
    try:
        msg = c.poll(1.0)

    except SerializerError as e:
        print("Message deserialization failed for {}: {}".format(msg, e))
        break

    if msg is None:
        continue

    if msg.error():
        print("AvroConsumer error: {}".format(msg.error()))
        continue


    key = msg.key().decode('utf-8')
    value = avro_serde.decode_message(msg.value())

    print(key, value)

    if msg.offset() + 1 == high:
        break


c.close()
