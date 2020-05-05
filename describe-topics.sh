#!/bin/sh

ZOOKEEPER=${ZOOKEEPER:=localhost:2181}

cd -P /opt/kafka/pro

bin/kafka-topics.sh --describe --zookeeper $ZOOKEEPER
