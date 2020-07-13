#!/bin/sh

KAFKA_HOME=${KAFKA_HOME:=/kafka}
KAFKA_BOOTSTRAP_SERVER=${KAFKA_BOOTSTRAP_SERVER:=kafka:9092}

cd -P $KAFKA_HOME

bin/kafka-consumer-groups.sh --bootstrap-server $KAFKA_BOOTSTRAP_SERVER --all-groups --describe
