#!/usr/bin/env python3

"""
    List Kafka topics
"""

from confluent_kafka.admin import AdminClient

import os


def list_topics() -> None:
    """
        List Kafka topics
    """
    bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    a = AdminClient({'bootstrap.servers': bootstrap_servers})

    md = a.list_topics(timeout=10)

    print("{} topics:".format(len(md.topics)))

    for t in iter(md.topics.values()):
        if t.error is not None:
            errstr = ": {}".format(t.error)
        else:
            errstr = ""

        print("  \"{}\" with {} partition(s){}".format(t, len(t.partitions), errstr))


if __name__ == "__main__":
    list_topics()
