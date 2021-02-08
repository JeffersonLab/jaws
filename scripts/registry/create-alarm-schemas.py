#!/usr/bin/env python3

import os, json

from confluent_kafka.schema_registry import SchemaRegistryClient, Schema, SchemaReference

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
client = SchemaRegistryClient(sr_conf)

def register(file, subject, references=[]):
    with open(file, 'r') as f:
        schema_str = f.read()

    unregistered_schema = Schema(schema_str, 'AVRO', references)

    id = client.register_schema(subject, unregistered_schema)

    print('Successfully registered {} with id: {}'.format(subject, id))

    registered_schema = client.get_latest_version(subject)

    return registered_schema

def process(record):
    if not record['file'].startswith('/'):
        record['file'] = projectpath + record['file']

    references = []

    for ref in record['references']:
        references.append(SchemaReference(ref['name'], ref['subject'], ref['version']))

    s = register(record['file'], record['subject'], references)

conf = os.environ.get('SCHEMA_CONFIG', projectpath + 'config/schemas.json')

with open(conf, 'r') as f:
    str = f.read()
    records = json.loads(str)
    for record in records:
        process(record)