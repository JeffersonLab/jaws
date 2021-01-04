#!/bin/bash

[ -z "$KAFKA_HOME" ] && echo "KAFKA_HOME environment required" && exit 1;

[ -z "$BOOTSTRAP_SERVER" ] && echo "BOOTSTRAP_SERVER environment required" && exit 1;

cd -P $KAFKA_HOME

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER \
             --delete \
             --topic registered-alarms

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER \
             --delete \
             --topic active-alarms

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER \
             --delete \
             --topic shelved-alarms

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER \
             --delete \
             --topic epics-channels
