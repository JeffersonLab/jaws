#!/usr/bin/env python3

import os, json

from confluent_kafka.schema_registry import SchemaRegistryClient

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
client = SchemaRegistryClient(sr_conf)

list = client.get_subjects();

for subject in list:
    registered = client.get_latest_version(subject)

    filename = "/tmp/schemas/" + registered.subject + ".avsc"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as text_file:
        print(json.dumps(json.loads(registered.schema.schema_str), indent=4), file=text_file)

    print("ID: {}, Subject: {}, Version: {}, File: {}".format(registered.schema_id, registered.subject, registered.version, filename))
