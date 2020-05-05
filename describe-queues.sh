#!/bin/sh

BOOTSTRAP_SERVERS=${BOOTSTRAP_SERVERS:=localhost:9092}

cd -P /opt/kafka/pro

bin/kafka-consumer-groups.sh --bootstrap-server $BOOTSTRAP_SERVERS --all-groups --describe
