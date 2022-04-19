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

    print(f"{len(groups)} consumer groups:")

    for group in groups:
        if group.error is not None:
            errstr = f": {group.error}"
        else:
            errstr = ""

        print(
            f" \"{group}\" mems: {len(group.members)}, pro: {group.protocol}, pro_type: {group.protocol_type}{errstr}")

        for member in group.members:
            print(f"id {member.id} client_id: {member.client_id} client_host: {member.client_host}")


if __name__ == "__main__":
    show_consumer_groups()
