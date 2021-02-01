#!/bin/sh

SCHEMA_REGISTRY=${SCHEMA_REGISTRY:=http://registry:8081}

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`


# Load AVRO schema file
data="$(cat $SCRIPT_DIR/../../schemas/active-alarms-key.avsc)"
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
            $SCHEMA_REGISTRY/subjects/active-alarms-key/versions


# Load AVRO schema file
data="$(cat $SCRIPT_DIR/../../schemas/registered-alarms-value.avsc)"
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
            $SCHEMA_REGISTRY/subjects/registered-alarms-value/versions


# Load AVRO schema file
data="$(cat $SCRIPT_DIR/../../schemas/active-alarms-value.avsc)"
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
            $SCHEMA_REGISTRY/subjects/active-alarms-value/versions


# Load AVRO schema file
data="$(cat $SCRIPT_DIR/../../schemas/shelved-alarms-value.avsc)"
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
            $SCHEMA_REGISTRY/subjects/shelved-alarms-value/versions