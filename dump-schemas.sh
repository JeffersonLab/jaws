#!/bin/sh

SCRIPT_DIR=/opt/kafka/scripts
OUT_DIR=/tmp/schema-cache

cd $SCRIPT_DIR
schemas=`./list-schemas.sh`

mkdir -p $OUT_DIR
cd $OUT_DIR

echo "Dumping all schemas to $OUT_DIR"

IFS=$'\n'
for schema in $schemas; do
    curl -s http://localhost:8081/subjects/$schema/versions/latest | jq -r '.schema|fromjson' > $schema.avsc
done
