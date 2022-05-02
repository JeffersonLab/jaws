#!/usr/bin/env python3

"""
    Describe a Specific JAWS AVRO schema and version in the Schema Registry
"""

import json
import os
import sys

from confluent_kafka.schema_registry import SchemaRegistryClient


def describe_version() -> None:
    """
        Describe a Specific JAWS AVRO schema and version in the Schema Registry
    """
    if len(sys.argv) != 3:
        print("Usage: ./describe_version.py <subject> <version>")
        sys.exit(1)

    subject = sys.argv[1]
    version = sys.argv[2]

    print(f"Describe {subject}; version {version}")

    sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    client = SchemaRegistryClient(sr_conf)

    registered = client.get_version(subject, version)

    filename = "/tmp/schemas/" + registered.subject + "-" + version + ".avsc"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as text_file:
        print(json.dumps(json.loads(registered.schema.schema_str), indent=4), file=text_file)
        print(
            f"ID: {registered.schema_id}, Subj: {registered.subject}, Ver: {registered.version}, File: {filename}")


if __name__ == "__main__":
    describe_version()
