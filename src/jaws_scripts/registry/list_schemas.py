#!/usr/bin/env python3

import os

from confluent_kafka.schema_registry import SchemaRegistryClient


def main() -> None:
    sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    client = SchemaRegistryClient(sr_conf)

    subjects = client.get_subjects()

    subjects.sort()

    for subject in subjects:
        print(subject)


if __name__ == "__main__":
    main()
