#!/usr/bin/env python3

import os
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

ts = time.time()

c = Consumer({
    'bootstrap.servers': bootstrap_servers,
    'group.id': 'client.py' + str(ts)})

def my_on_assign(consumer, partitions):
    global highOffsets

    highOffsets = {}

    for p in partitions:
        p.offset = OFFSET_BEGINNING
        low, high = c.get_watermark_offsets(p)
        highOffsets[p.topic] = high
    consumer.assign(partitions)

c.subscribe(['registered-alarms','active-alarms','shelved-alarms'], on_assign=my_on_assign)

registered = {}
active = {}
shelved = {}

registeredLoaded = False
activeLoaded = False
shelvedLoaded = False

class ContinueException(Exception):
  pass

def poll_msg(): 
    global activeLoaded
    global shelvedLoaded
    global registeredLoaded
    global highOffsets

    print('polling')

    msg = c.poll(1.0)

    if msg is None or msg.error():
      print('None msg')
      return [msg, None] 

    topic = msg.topic()
    key = msg.key().decode('utf-8')
    value = avro_serde.decode_message(msg.value())

    print(topic, key, value)

    if topic == "registered-alarms":
      registered[key] = value

      if msg.offset() + 1 == highOffsets["registered"]:
        registeredLoaded = True

    elif topic == "active-alarms":
      active[key] = value

      if msg.offset() + 1 == highOffsets["active-alarms"]:
        activeLoaded = True

    elif topic == "shelved-alarms":
        shelved[key] = value

        if msg.offset() + 1 == highOffsets["shelved-alarms"]:
            shelvedLoaded = True

    else:
      print("Unknown topic {}", topic)

    #print(topic, key, value)
    return [msg, key]

noneCount = 0

while True:
  if noneCount > 10:  
    raise RuntimeError("Timeout: taking too long to obtain initial state")

  try:
    msg, key = poll_msg()
  except SerializerError as e:
    print("Message deserialization failed for {}".format(e))
    raise 

  if msg is None:
    noneCount = noneCount + 1
    continue

  if msg.error():
    print("Continuing {}: {}".format(msg, msg.error()))
    continue

  if registeredLoaded and shelvedLoaded and activeLoaded:
    break

# At this point the initial flurry of messages have been read up to the high water mark offsets read moments ago.  Now we can report somewhat up-to-date snapshot of system state and start monitoring for anything that has happened since reading high water mark or anything coming in the future
print("Initial State:")
for key in active:
   if active.get(key):
     print(key, active.get(key), "shelved:", shelved.get(key), "info:", registered.get(key))

print("Continuing to monitor: ")
while True:
  try:
    msg, key  = poll_msg()
  except SerializerError as e:
    print("Message deserialization failed for {}".format(e))
    break
  
  if msg is None:
    continue

  if msg.error():
    print("Continuing {}: {}".format(msg, msg.error()))
    continue 

  if active.get(key):
    print(key, active.get(key), "shelved:", shelved.get(key), "info:", registered.get(key))
  else:
    print(key, "No longer alarming")

c.close()
