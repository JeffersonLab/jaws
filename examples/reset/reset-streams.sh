#!/bin/sh

${KAFKA_HOME}/bin/kafka-streams-application-reset.sh --input-topics alarm-instances --bootstrap-servers kafka1:9092 --application-id registrations2epics
${KAFKA_HOME}/bin/kafka-streams-application-reset.sh --input-topics alarm-activations --bootstrap-servers kafka1:9092 --application-id jaws-effective-processor