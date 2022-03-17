#!/usr/bin/env python3

"""
    Create JAWS Kafka topics
"""

from confluent_kafka.admin import AdminClient, NewTopic

import os
import json
import pkgutil


def create_topics() -> None:
    """
        Create JAWS Kafka topics
    """
    bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    a = AdminClient({'bootstrap.servers': bootstrap_servers})

    conf = pkgutil.get_data("jaws_libp", "avro/topics.json")

    topics = json.loads(conf)

    new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1,
                           config={"cleanup.policy": "compact"}) for topic in topics]

    fs = a.create_topics(new_topics, operation_timeout=15)

    for topic, f in fs.items():
        try:
            f.result()
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))


if __name__ == "__main__":
    create_topics()
