#!/bin/bash

KAFKA_HOME=${KAFKA_HOME:=/kafka}
KAFKA_BOOTSTRAP_SERVER=${KAFKA_BOOTSTRAP_SERVER:=kafka:9092}

cd -P $KAFKA_HOME

bin/kafka-topics.sh --bootstrap-server $KAFKA_BOOTSTRAP_SERVER \
             --create \
             --topic registered-alarms \
             --config cleanup.policy=compact \
             --config min.cleanable.dirty.ratio=0.01 \
             --config delete.retention.ms=100 \
             --config segment.ms=100

bin/kafka-topics.sh --bootstrap-server $KAFKA_BOOTSTRAP_SERVER \
             --create \
             --topic active-alarms \
             --config cleanup.policy=compact \
             --config min.cleanable.dirty.ratio=0.01 \
             --config delete.retention.ms=100 \
             --config segment.ms=100

bin/kafka-topics.sh --bootstrap-server $KAFKA_BOOTSTRAP_SERVER \
             --create \
             --topic shelved-alarms \
             --config cleanup.policy=compact \
             --config min.cleanable.dirty.ratio=0.01 \
             --config delete.retention.ms=100 \
             --config segment.ms=100
