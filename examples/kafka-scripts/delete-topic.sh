#!/bin/sh

if [[ $# -eq 0 ]] ; then
    echo 'Topic name required'
    exit 1
fi

[ -z "$KAFKA_HOME" ] && echo "KAFKA_HOME environment required" && exit 1;

[ -z "$BOOTSTRAP_SERVER" ] && echo "BOOTSTRAP_SERVER environment required" && exit 1;

cd -P $KAFKA_HOME

bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER --delete --topic $1

