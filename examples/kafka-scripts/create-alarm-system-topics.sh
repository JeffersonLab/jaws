#!/bin/bash

/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 \
             --create \
             --topic alarms \
             --config cleanup.policy=compact \
             --config min.cleanable.dirty.ratio=0.01 \
             --config delete.retention.ms=100 \
             --config segment.ms=100

/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 \
             --create \
             --topic active-alarms \
             --config cleanup.policy=compact \
             --config min.cleanable.dirty.ratio=0.01 \
             --config delete.retention.ms=100 \
             --config segment.ms=100

/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 \
             --create \
             --topic shelved-alarms \
             --config cleanup.policy=compact \
             --config min.cleanable.dirty.ratio=0.01 \
             --config delete.retention.ms=100 \
             --config segment.ms=100
