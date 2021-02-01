#!/bin/sh

SCHEMA_REGISTRY=${SCHEMA_REGISTRY:=http://registry:8081}

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`
DMP_DIR=${DMP_DIR:=/tmp/schema-cache}

cd $SCRIPT_DIR
schemas=`./list-schemas.sh`

mkdir -p $DMP_DIR
cd $DMP_DIR

echo "Dumping all schemas to $DMP_DIR"

IFS=$'\n'
for schema in $schemas; do
    curl -s $SCHEMA_REGISTRY/subjects/$schema/versions/latest | jq -r '.schema|fromjson' > $schema.avsc
done
