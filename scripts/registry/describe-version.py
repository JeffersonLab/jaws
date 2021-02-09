#!/usr/bin/env python3

import os, json, sys

from confluent_kafka.schema_registry import SchemaRegistryClient

if len(sys.argv) != 3:
   print("Usage: ./describe-version.py <subject> <version>")
   quit()

subject = sys.argv[1]
version = sys.argv[2]

print("Describe {}; version {}".format(subject, version))

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
client = SchemaRegistryClient(sr_conf)


registered = client.get_version(subject, version)

filename = "/tmp/schemas/" + registered.subject + "-" + version + ".avsc"
os.makedirs(os.path.dirname(filename), exist_ok=True)
with open(filename, "w") as text_file:
  print(json.dumps(json.loads(registered.schema.schema_str), indent=4), file=text_file)

  print("ID: {}, Subject: {}, Version: {}, File: {}".format(registered.schema_id, registered.subject, registered.version, filename))
