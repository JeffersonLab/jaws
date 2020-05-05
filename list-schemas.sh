#!/bin/sh

SCHEMA_REGISTRY=${SCHEMA_REGISTRY:=http://localhost:8081}

curl -s -X GET -w "\n" $SCHEMA_REGISTRY/subjects | jq -r '.[]'

