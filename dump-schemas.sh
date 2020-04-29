#!/bin/sh

DIR=/tmp/schema-cache
TOPIC=alarms

mkdir -p $DIR
cd $DIR

echo "Dumping all schemas to $DIR"

schemas=`/opt/kafka/scripts/list-schemas.sh`

IFS=$'\n'
for schema in $schemas; do
    curl -s http://localhost:8081/subjects/$schema/versions/latest | jq -r '.schema|fromjson' > $schema.avsc
done
