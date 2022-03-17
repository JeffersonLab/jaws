#!/usr/bin/env python3

"""
    Delete JAWS Kafka topics
"""

from confluent_kafka.admin import AdminClient

import os
import json
import pkgutil


def delete_topics() -> None:
    """
        Delete JAWS Kafka topics
    """
    bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    a = AdminClient({'bootstrap.servers': bootstrap_servers})

    conf = pkgutil.get_data("jaws_libp", "avro/topics.json")

    topics = json.loads(conf)

    fs = a.delete_topics(topics, operation_timeout=15)

    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} deleted".format(topic))
        except Exception as e:
            print("Failed to delete topic {}: {}".format(topic, e))


if __name__ == "__main__":
    delete_topics()
