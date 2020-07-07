#!/bin/sh

KAFKA_HOME=${KAFKA_HOME:=/opt/kafka/pro}
BOOTSTRAP_SERVERS=${BOOTSTRAP_SERVERS:=localhost:9092}

cd -P $KAFKA_HOME

bin/kafka-consumer-groups.sh --bootstrap-server $BOOTSTRAP_SERVERS --all-groups --describe
