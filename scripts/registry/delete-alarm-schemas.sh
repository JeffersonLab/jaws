#!/bin/sh

SCHEMA_REGISTRY=${SCHEMA_REGISTRY:=http://registry:8081}

curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/registered-alarms-key | jq -r '.[]'
curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/registered-alarms-key?permanent=true | jq -r '.[]'

curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/registered-alarms-value | jq -r '.[]'
curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/registered-alarms-value?permanent=true | jq -r '.[]'

curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/active-alarms-value | jq -r '.[]'
curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/active-alarms-value?permanent=true | jq -r '.[]'

curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/shelved-alarms-value | jq -r '.[]'
curl -s -X DELETE -w "\n" $SCHEMA_REGISTRY/subjects/shelved-alarms-value?permanent=true | jq -r '.[]'