#!/bin/sh

SCHEMA_REGISTRY=${SCHEMA_REGISTRY:=http://registry:8081}

SCRIPT_DIR=`dirname "$(readlink -f "$0")"`


data="$(cat $SCRIPT_DIR/../../schemas/active-alarms-key.avsc)"
data="{\"schema\":
$data
}"
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
            --data "$data" \
            $SCHEMA_REGISTRY/subjects/registered-alarms-key/versions


data="$(cat $SCRIPT_DIR/../../schemas/registered-alarms-value.avsc)"
data="{\"schema\":
$data
}"
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
            --data "$data" \
            $SCHEMA_REGISTRY/subjects/registered-alarms-value/versions


data="$(cat $SCRIPT_DIR/../../schemas/active-alarms-value.avsc)"
data="{\"schema\":
$data
}"
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
            --data "$data" \
            $SCHEMA_REGISTRY/subjects/active-alarms-value/versions


data="$(cat $SCRIPT_DIR/../../schemas/shelved-alarms-value.avsc)"
data="{\"schema\":
$data
}"
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
            --data "$data" \
            $SCHEMA_REGISTRY/subjects/shelved-alarms-value/versions