#!/bin/sh

SCHEMA_REGISTRY=${SCHEMA_REGISTRY:=http://registry:8081}

curl -s -X GET -w "\n" $SCHEMA_REGISTRY/subjects | jq -r '.[]'

