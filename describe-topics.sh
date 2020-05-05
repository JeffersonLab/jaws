#!/bin/sh

KAFKA_HOME=${KAFKA_HOME:=/opt/kafka/pro}
ZOOKEEPER=${ZOOKEEPER:=localhost:2181}

cd -P $KAFKA_HOME

bin/kafka-topics.sh --describe --zookeeper $ZOOKEEPER
