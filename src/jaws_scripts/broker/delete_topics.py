#!/usr/bin/env python3

"""
    Delete JAWS Kafka topics
"""

import json
import os
import pkgutil

from confluent_kafka.admin import AdminClient


def delete_topics() -> None:
    """
        Delete JAWS Kafka topics
    """
    bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    conf = pkgutil.get_data("jaws_libp", "avro/topics.json")

    topics = json.loads(conf)

    futures = admin_client.delete_topics(topics, operation_timeout=15)

    for topic, future in futures.items():
        try:
            future.result()  # The result itself is None
            print(f"Topic {topic} deleted")
        except Exception as e:
            print(f"Failed to delete topic {topic}: {e}")


if __name__ == "__main__":
    delete_topics()
