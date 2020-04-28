#!/bin/sh

curl -s -X GET -w "\n" http://localhost:8081/subjects | jq -r '.[]'

