#!/usr/bin/env python3

"""
    Register JAWS AVRO schemas in to Schema Registry
"""

import json
import os
import pkgutil
import traceback

from confluent_kafka.schema_registry import SchemaRegistryClient, Schema, SchemaReference, SchemaRegistryError

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
client = SchemaRegistryClient(sr_conf)


def __register(file, subject, references=[]):

    schema_bytes = pkgutil.get_data("jaws_libp", file)

    json_dict = json.loads(schema_bytes)

    json_str = json.dumps(json_dict)

    unregistered_schema = Schema(json_str, 'AVRO', references)

    id = client.register_schema(subject, unregistered_schema)

    print('Successfully registered {} with id: {}'.format(subject, id))

    registered_schema = client.get_latest_version(subject)

    return registered_schema


def __process(record):
    references = []

    for ref in record['references']:
        references.append(SchemaReference(ref['name'], ref['subject'], ref['version']))

    try:
        s = __register(record['file'], record['subject'], references)
    except SchemaRegistryError:
        print('Unable to create subject {}'.format(record['subject']))
        traceback.print_exc()


def create_schemas() -> None:
    """
        Register JAWS AVRO schemas in to Schema Registry
    """
    conf = pkgutil.get_data("jaws_libp", "avro/schema-registry.json")

    records = json.loads(conf)
    for r in records:
        __process(r)


if __name__ == "__main__":
    create_schemas()
