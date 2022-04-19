#!/usr/bin/env python3

"""
    List Kafka topics
"""

import os

from confluent_kafka.admin import AdminClient


def list_topics() -> None:
    """
        List Kafka topics
    """
    bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    meta = admin_client.list_topics(timeout=10)

    print("{} topics:".format(len(meta.topics)))

    for topic in iter(meta.topics.values()):
        if topic.error is not None:
            errstr = ": {}".format(topic.error)
        else:
            errstr = ""

        print("  \"{}\" with {} partition(s){}".format(topic, len(topic.partitions), errstr))


if __name__ == "__main__":
    list_topics()
