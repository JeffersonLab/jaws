#!/bin/sh

SCHEMA_REGISTRY=${SCHEMA_REGISTRY:=http://registry:8081}

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`

PROJECT_DIR=$SCRIPT_DIR/..

while read path;
do 
name=$(basename $path)
echo Creating $name

# Load AVRO schema file
data="$(cat $PROJECTDIR/$path.avsc)"
# Replace " with /"
data="${data//\"/\\\"}"
# Replace Windows newlines with space
data="${data//$'\r\n'/ }"
# Replace UNIX newlines with space
data="${data//$'\n'/ }"
# Wrap contents in new JSON object literal
data="{\"schema\": \" $data \"}"

curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
            --data "$data" \
            $SCHEMA_REGISTRY/subjects/$name/versions

done < $SCRIPT_DIR/schemas.list

