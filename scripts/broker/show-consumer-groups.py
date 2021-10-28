#!/usr/bin/env python3

from confluent_kafka.admin import AdminClient

import os

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

a = AdminClient({'bootstrap.servers': bootstrap_servers})

groups = a.list_groups(timeout=10)

print("{} consumer groups:".format(len(groups)))

for g in groups:
    if g.error is not None:
        errstr = ": {}".format(g.error)
    else:
        errstr = ""

    print(" \"{}\" with {} member(s), protocol: {}, protocol_type: {}{}".format(
            g, len(g.members), g.protocol, g.protocol_type, errstr))

    for m in g.members:
        print("id {} client_id: {} client_host: {}".format(m.id, m.client_id, m.client_host))

