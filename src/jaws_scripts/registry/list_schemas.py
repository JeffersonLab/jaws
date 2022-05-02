#!/usr/bin/env python3

"""
    List all schemas in the Schema Registry
"""

import os

from confluent_kafka.schema_registry import SchemaRegistryClient


def list_schemas() -> None:
    """
        List all schemas in the Schema Registry
    """
    sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    client = SchemaRegistryClient(sr_conf)

    subjects = client.get_subjects()

    subjects.sort()

    for subject in subjects:
        print(subject)


if __name__ == "__main__":
    list_schemas()
