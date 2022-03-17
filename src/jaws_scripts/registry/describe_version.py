#!/usr/bin/env python3

"""
    Describe a Specific JAWS AVRO schema and version in the Schema Registry
"""

import os
import json
import sys

from confluent_kafka.schema_registry import SchemaRegistryClient


def describe_version() -> None:
    """
        Describe a Specific JAWS AVRO schema and version in the Schema Registry
    """
    if len(sys.argv) != 3:
        print("Usage: ./describe_version.py <subject> <version>")
        quit()

    subject = sys.argv[1]
    version = sys.argv[2]

    print("Describe {}; version {}".format(subject, version))

    sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    client = SchemaRegistryClient(sr_conf)

    registered = client.get_version(subject, version)

    filename = "/tmp/schemas/" + registered.subject + "-" + version + ".avsc"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as text_file:
        print(json.dumps(json.loads(registered.schema.schema_str), indent=4), file=text_file)
        print("ID: {}, Subject: {}, Version: {}, File: {}".format(registered.schema_id, registered.subject,
                                                                  registered.version, filename))


if __name__ == "__main__":
    describe_version()
