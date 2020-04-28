#!/bin/sh

DIR=/tmp/schema-cache
TOPIC=alarms

mkdir -p $DIR
cd $DIR

echo "Dumping all schemas to $DIR"

curl -s http://localhost:8081/subjects/$TOPIC-value/versions/latest | jq -r '.schema|fromjson' > $TOPIC-value.avsc
