#!/bin/sh

KAFKA_HOME=${KAFKA_HOME:=/kafka}
KAFKA_BOOTSTRAP_SERVER=${KAFKA_BOOTSTRAP_SERVER:=kafka:9092}

cd -P $KAFKA_HOME

bin/kafka-topics.sh --list --bootstrap-server $KAFKA_BOOTSTRAP_SERVER
