#!/usr/bin/env python3

"""
    Describe JAWS AVRO schemas in to Schema Registry
"""

import os
import json
import pkgutil

from confluent_kafka.schema_registry import SchemaRegistryClient


def describe_schemas() -> None:
    """
        Describe JAWS AVRO schemas in to Schema Registry
    """
    sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    client = SchemaRegistryClient(sr_conf)

    conf = pkgutil.get_data("jlab_jaws", "avro/schema-registry.json")

    records = json.loads(conf)

    lookup = {}

    for r in records:
        lookup[r['subject']] = r['file']

    subjects = client.get_subjects()

    for subject in subjects:
        registered = client.get_latest_version(subject)

        filename = 'avro/schemas/' + registered.subject + '.avsc'

        if registered.subject in lookup:
            filename = lookup[registered.subject]

        path = "/tmp/" + filename
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as text_file:
            print(json.dumps(json.loads(registered.schema.schema_str), indent=4), file=text_file)

        print("ID: {}, Subject: {}, Version: {}, File: {}".format(registered.schema_id, registered.subject, registered.version, path))


if __name__ == "__main__":
    describe_schemas()
