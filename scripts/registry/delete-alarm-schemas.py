#!/usr/bin/env python3

import os, json

from confluent_kafka.schema_registry import SchemaRegistryClient

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
client = SchemaRegistryClient(sr_conf)

def process(record):
    list = client.delete_subject(record['subject'])

    print('Successfully deleted {}; versions: {}'.format(record['subject'], list))

conf = os.environ.get('SCHEMA_CONFIG', projectpath + 'config/schema-registry.json')

with open(conf, 'r') as f:
    str = f.read()
    records = json.loads(str)
    for record in records:
        process(record)