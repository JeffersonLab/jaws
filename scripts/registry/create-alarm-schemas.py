#!/usr/bin/env python3

import json
import os
import pkgutil

from confluent_kafka.schema_registry import SchemaRegistryClient, Schema, SchemaReference

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
client = SchemaRegistryClient(sr_conf)


def register(file, subject, references=[]):

    schema_bytes = pkgutil.get_data("jlab_jaws", file)

    json_dict = json.loads(schema_bytes)

    json_str = json.dumps(json_dict)

    unregistered_schema = Schema(json_str, 'AVRO', references)

    id = client.register_schema(subject, unregistered_schema)

    print('Successfully registered {} with id: {}'.format(subject, id))

    registered_schema = client.get_latest_version(subject)

    return registered_schema


def process(record):
    references = []

    for ref in record['references']:
        references.append(SchemaReference(ref['name'], ref['subject'], ref['version']))

    s = register(record['file'], record['subject'], references)


conf = pkgutil.get_data("jlab_jaws", "avro/schema-registry.json")

records = json.loads(conf)
for r in records:
    process(r)
