#!/usr/bin/env python3

from confluent_kafka.admin import AdminClient, ConfigResource, ConfigSource
from confluent_kafka import KafkaException

import os
import json
import pkgutil

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

a = AdminClient({'bootstrap.servers': bootstrap_servers})

conf = pkgutil.get_data("jlab_jaws", "avro/topics.json")

topics = json.loads(conf)


def print_config(config, depth):
    print('%40s = %-50s' %
          ((' ' * depth) + config.name, config.value))


resources = []

for t in topics:
    resources.append(ConfigResource('topic', t))

fs = a.describe_configs(resources)

for res, f in fs.items():
    try:
        configs = f.result()
        print("")
        print("Topic {}".format(res.name))
        print("-----------------------------------------------------------------")
        for config in iter(configs.values()):
            print_config(config, 1)
    except KafkaException as e:
        print("Failed to describe {}: {}".format(res, e))
    except Exception:
        raise
