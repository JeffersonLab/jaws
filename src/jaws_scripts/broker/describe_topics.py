#!/usr/bin/env python3

"""
    Describe Kafka topics
"""

import json
import os
import pkgutil

from confluent_kafka import KafkaException
from confluent_kafka.admin import AdminClient, ConfigResource


def describe_topics() -> None:
    """
        Describe Kafka topics
    """
    bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    conf = pkgutil.get_data("jaws_libp", "avro/topics.json")

    topics = json.loads(conf)

    def print_config(config, depth):
        print(f'{(" " * depth) + config.name:>40} = {config.value:<50}')

    resources = []

    for topic in topics:
        resources.append(ConfigResource('topic', topic))

    futures = admin_client.describe_configs(resources)

    for res, future in futures.items():
        try:
            configs = future.result()
            print("")
            print(f"Topic {res.name}")
            print("-----------------------------------------------------------------")
            for config in iter(configs.values()):
                print_config(config, 1)
        except KafkaException as e:
            print(f"Failed to describe {res}: {e}")


if __name__ == "__main__":
    describe_topics()
