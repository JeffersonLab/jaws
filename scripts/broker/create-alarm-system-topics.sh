#!/bin/bash

[ -z "$KAFKA_HOME" ] && echo "KAFKA_HOME environment required" && exit 1;

[ -z "$BOOTSTRAP_SERVER" ] && echo "BOOTSTRAP_SERVER environment required" && exit 1;

cd -P $KAFKA_HOME

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER \
             --create \
             --topic registered-alarms \
             --config cleanup.policy=compact

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER \
             --create \
             --topic active-alarms \
             --config cleanup.policy=compact

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER \
             --create \
             --topic shelved-alarms \
             --config cleanup.policy=compact

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER \
             --create \
             --topic epics-channels \
             --config cleanup.policy=compact

