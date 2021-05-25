#!/usr/bin/env python3

from confluent_kafka.admin import AdminClient
from confluent_kafka import KafkaException

import os

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

a = AdminClient({'bootstrap.servers': bootstrap_servers})

topics = ['registered-alarms', 'active-alarms', 'overridden-alarms', 'registered-classes', 'alarm-state']

fs = a.delete_topics(topics, operation_timeout=15)

for topic, f in fs.items():
    try:
        f.result()  # The result itself is None
        print("Topic {} deleted".format(topic))
    except Exception as e:
        print("Failed to delete topic {}: {}".format(topic, e))
