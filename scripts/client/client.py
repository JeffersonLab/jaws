#!/usr/bin/env python3

import os
import time
import json

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
    global topicLoaded

    highOffsets = {}

    for p in partitions:
        p.offset = OFFSET_BEGINNING
        low, high = c.get_watermark_offsets(p)
        highOffsets[p.topic] = high
        print(p.topic, low, high)
        if high == 0:
            topicLoaded[p.topic] = True
    consumer.assign(partitions)

c.subscribe(['registered-alarms','active-alarms','shelved-alarms'], on_assign=my_on_assign)

msgState = {
  'registered-alarms': {},
  'Alarming': {},
  'Ack': {},
  'AlarmingEPICS' : {},
  'AckEPICS' : {},
  'shelved-alarms': {}
}

topicLoaded = {
  'registered-alarms': False,
  'active-alarms': False,
  'shelved-alarms': False
}

def poll_msg(): 
    global topicLoaded
    global highOffsets

    print('polling')

    msg = c.poll(1.0)

    if msg is None or msg.error():
      print('None msg')
      return [msg, None]

    topic = msg.topic()

    if topic == 'active-alarms':
        key = avro_serde.decode_message(msg.key())
        alarmname = key['name']
        msgtype = key['type']
    else:
        key = msg.key().decode('utf-8')
        alarmname = key
        msgtype = topic

    value = avro_serde.decode_message(msg.value())
    timestamp = msg.timestamp()
    headers = msg.headers()

    print(topic, key, value)

    msgState[msgtype][alarmname] = (timestamp, headers, value)

    # Clear most recent ack on new alarming instance
    if msgtype == 'Alarming' and value != None:
        msgState['Ack'].pop(alarmname, None)

    # Clear most recent ackEPICS on new alarming instance
    if msgtype == 'AlarmingEPICS' and value['msg']['sevr'] in ["MINOR", "MAJOR"]:
        msgState['AckEPICS'].pop(alarmname, None)

    if msg.offset() + 1 == highOffsets[topic]:
        topicLoaded[topic] = True

    #print(topic, key, value)
    return [msg, alarmname]

def state_str(state):
  str = ''

  #print('state: ', state)

  timestamp = state[0]
  headers = state[1]
  value = state[2]

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

  jvalue = json.dumps(value)

  str = '[' + ts + ', ' + user + ', ' + producer + ', ' + host + ', ' + jvalue + ']'

  return str

def disp_alarm(key):
  registered = msgState['registered-alarms'].get(key)
  shelved = msgState['shelved-alarms'].get(key)

  alarming = msgState['Alarming'].get(key)
  ack = msgState['Ack'].get(key)
  alarmingEPICS = msgState['AlarmingEPICS'].get(key)
  ackEPICS = msgState['AckEPICS'].get(key)

  if registered:
    registeredInfo = state_str(registered)
  else:
    registeredInfo = 'None'

  if alarming:
      alarmingInfo = state_str(alarming)
  elif alarmingEPICS:
      alarmingInfo = state_str(alarmingEPICS)
  else:
      alarmingInfo = 'None'

  if ack:
      ackInfo = state_str(ack)
  elif ackEPICS:
      ackInfo = state_str(ackEPICS)
  else:
      ackInfo = 'None'

  if shelved:
      shelvedInfo = state_str(shelved)
  else:
      shelvedInfo = 'None'

  print(key, 'Reg: ', registeredInfo, 'Alm: ', alarmingInfo, 'Ack: ', ackInfo, 'Shel: ', shelvedInfo)

noneCount = 0

while True:
  if noneCount > 10:  
    raise RuntimeError("Timeout: taking too long to obtain initial state")

  try:
    msg, alarmname = poll_msg()
  except SerializerError as e:
    print("Message deserialization failed for {}".format(e))
    raise 

  if msg is None:
    noneCount = noneCount + 1
    continue

  if msg.error():
    print("Continuing {}: {}".format(msg, msg.error()))
    continue

  if topicLoaded['registered-alarms'] and topicLoaded['active-alarms'] and topicLoaded['shelved-alarms']:
    break

# At this point the initial flurry of messages have been read up to the high water mark offsets read moments ago.  Now we can report somewhat up-to-date snapshot of system state and start monitoring for anything that has happened since reading high water mark or anything coming in the future
print("Initial State:")
for alarmname in msgState['Alarming']:
  disp_alarm(alarmname)

for alarmname in msgState['AlarmingEPICS']:
    disp_alarm(alarmname)

print("Continuing to monitor: ")
while True:
  try:
    msg, alarmname  = poll_msg()
  except SerializerError as e:
    print("Message deserialization failed for {}".format(e))
    break
  
  if msg is None:
    continue

  if msg.error():
    print("Continuing {}: {}".format(msg, msg.error()))
    continue 

  disp_alarm(alarmname)

c.close()
