#!/usr/bin/env python3

"""
    Show Kafka consumer groups
"""

import os

from confluent_kafka.admin import AdminClient


def show_consumer_groups() -> None:
    """
        Show Kafka consumer groups
    """
    bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    groups = admin_client.list_groups(timeout=10)

    print("{} consumer groups:".format(len(groups)))

    for group in groups:
        if group.error is not None:
            errstr = ": {}".format(group.error)
        else:
            errstr = ""

        print(" \"{}\" with {} member(s), protocol: {}, protocol_type: {}{}".format(
            group, len(group.members), group.protocol, group.protocol_type, errstr))

        for member in group.members:
            print("id {} client_id: {} client_host: {}".format(member.id, member.client_id, member.client_host))


if __name__ == "__main__":
    show_consumer_groups()
