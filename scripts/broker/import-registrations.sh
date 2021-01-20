#!/bin/sh

[ -z "$CONFLUENT_HOME" ] && echo "CONFLUENT_HOME environment required" && exit 1;

[ -z "$BOOTSTRAP_SERVER" ] && echo "BOOTSTRAP_SERVER environment required" && exit 1;

[ -z "$SCHEMA_REGISTRY" ] && echo "SCHEMA_REGISTRY environment required" && exit 1;

CWD=$(readlink -f "$(dirname "$0")")

FILE=$1

[ ! -f "$FILE" ] && echo "File to import not found" && exit 1; 

$CONFLUENT_HOME/bin/kafka-avro-console-producer --bootstrap-server=$BOOTSTRAP_SERVER \
                                  --topic registered-alarms \
                                  --property parse.key=true \
                                  --property key.separator== \
                                  --property key.serializer=org.apache.kafka.common.serialization.StringSerializer \
                                  --property schema.registry.url=$SCHEMA_REGISTRY \
                                  --property value.schema.file=$CWD/../../schemas/registered-alarms-value.avsc < $FILE

