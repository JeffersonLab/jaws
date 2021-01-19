#!/bin/sh

[ -z "$KAFKA_HOME" ] && echo "KAFKA_HOME environment required" && exit 1;

[ -z "$BOOTSTRAP_SERVER" ] && echo "BOOTSTRAP_SERVER environment required" && exit 1;

$KAFKA_HOME/bin/kafka-consumer-groups.sh --bootstrap-server $BOOTSTRAP_SERVER --all-groups --describe
