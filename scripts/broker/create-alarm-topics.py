#!/usr/bin/env python3

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException

import os

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

a = AdminClient({'bootstrap.servers': bootstrap_servers})

topics = ['registered-alarms', 'active-alarms', 'overridden-alarms', 'registered-classes', 'alarm-state']

new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1, config={"cleanup.policy": "compact"}) for topic in topics]

fs = a.create_topics(new_topics, operation_timeout=15)

for topic, f in fs.items():
    try:
        f.result()
        print("Topic {} created".format(topic))
    except Exception as e:
        print("Failed to create topic {}: {}".format(topic, e))
