#!/usr/bin/env python3

from confluent_kafka.admin import AdminClient

import os

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

a = AdminClient({'bootstrap.servers': bootstrap_servers})

md = a.list_topics(timeout=10)

print("{} topics:".format(len(md.topics)))

for t in iter(md.topics.values()):
    if t.error is not None:
        errstr = ": {}".format(t.error)
    else:
        errstr = ""

    print("  \"{}\" with {} partition(s){}".format(t, len(t.partitions), errstr))

