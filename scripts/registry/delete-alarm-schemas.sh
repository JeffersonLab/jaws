#!/bin/sh

SCHEMA_REGISTRY=${SCHEMA_REGISTRY:=http://registry:8081}

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`

PROJECT_DIR=$SCRIPT_DIR/..

while read path;
do
name=$(basename $path)
echo Deleting $name

curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/$name | jq -r '.[]'
curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/$name?permanent=true | jq -r '.[]'

done < $SCRIPT_DIR/schemas.list