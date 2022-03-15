#!/usr/bin/env python3

from confluent_kafka.admin import AdminClient, NewTopic

import os
import json
import pkgutil

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

a = AdminClient({'bootstrap.servers': bootstrap_servers})

conf = pkgutil.get_data("jlab_jaws", "avro/topics.json")

topics = json.loads(conf)

new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1, config={"cleanup.policy": "compact"}) for topic in topics]

fs = a.create_topics(new_topics, operation_timeout=15)

for topic, f in fs.items():
    try:
        f.result()
        print("Topic {} created".format(topic))
    except Exception as e:
        print("Failed to create topic {}: {}".format(topic, e))
