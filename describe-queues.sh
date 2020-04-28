#!/bin/sh

cd -P /opt/kafka/pro

bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --all-groups --describe
