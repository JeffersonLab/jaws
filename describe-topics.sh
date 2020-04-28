#!/bin/sh

cd -P /opt/kafka/pro

bin/kafka-topics.sh --describe --zookeeper localhost:2181
