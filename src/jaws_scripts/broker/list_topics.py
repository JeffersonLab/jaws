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

    print(f"{len(meta.topics)} topics:")

    for topic in iter(meta.topics.values()):
        if topic.error is not None:
            errstr = f": {topic.error}"
        else:
            errstr = ""

        print(f"  \"{topic}\" with {len(topic.partitions)} partition(s){errstr}")


if __name__ == "__main__":
    list_topics()
