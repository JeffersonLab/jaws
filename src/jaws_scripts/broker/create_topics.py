#!/usr/bin/env python3

"""
    Create JAWS Kafka topics
"""

import json
import os
import pkgutil

from confluent_kafka.admin import AdminClient, NewTopic


def create_topics() -> None:
    """
        Create JAWS Kafka topics
    """
    bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    conf = pkgutil.get_data("jaws_libp", "avro/topics.json")

    topics = json.loads(conf)

    new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1,
                           config={"cleanup.policy": "compact"}) for topic in topics]

    futures = admin_client.create_topics(new_topics, operation_timeout=15)

    for topic, future in futures.items():
        try:
            future.result()
            print(f"Topic {topic} created")
        except Exception as e:
            print(f"Failed to create topic {topic}: {e}")


if __name__ == "__main__":
    create_topics()
