#!/usr/bin/env python3

"""
    Register JAWS AVRO schemas in to Schema Registry
"""

import json
import os
import pkgutil
import traceback

from confluent_kafka.schema_registry import SchemaRegistryClient, Schema, SchemaReference, SchemaRegistryError

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
client = SchemaRegistryClient(sr_conf)


def __register(file, subject, references=None):
    if references is None:
        references = []

    schema_bytes = pkgutil.get_data("jaws_libp", file)

    json_dict = json.loads(schema_bytes)

    json_str = json.dumps(json_dict)

    unregistered_schema = Schema(json_str, 'AVRO', references)

    schema_id = client.register_schema(subject, unregistered_schema)

    print(f'Successfully registered {subject} with id: {schema_id}')

    registered_schema = client.get_latest_version(subject)

    return registered_schema


def __process(record):
    references = []

    for ref in record['references']:
        references.append(SchemaReference(ref['name'], ref['subject'], ref['version']))

    try:
        __register(record['file'], record['subject'], references)
    except SchemaRegistryError:
        print(f'Unable to create subject {record["subject"]}')
        traceback.print_exc()


def create_schemas() -> None:
    """
        Register JAWS AVRO schemas in to Schema Registry
    """
    conf = pkgutil.get_data("jaws_libp", "avro/schema-registry.json")

    records = json.loads(conf)
    for record in records:
        __process(record)


if __name__ == "__main__":
    create_schemas()
