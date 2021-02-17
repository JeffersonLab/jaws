#!/usr/bin/env python3

import os, json

from confluent_kafka.schema_registry import SchemaRegistryClient

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
client = SchemaRegistryClient(sr_conf)

list = client.get_subjects();

for subject in list:
    print(subject)
