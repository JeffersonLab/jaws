#!/bin/sh

cd -P /opt/kafka/pro

bin/kafka-topics.sh --list --zookeeper localhost:2181
