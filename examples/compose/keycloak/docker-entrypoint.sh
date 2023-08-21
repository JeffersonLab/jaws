#!/bin/bash

echo "--------------------------"
echo "| Step 1: Start Keycloak |"
echo "--------------------------"

/opt/keycloak/bin/kc.sh start-dev --hostname $KEYCLOAK_FRONTEND_HOSTNAME --hostname-port=$KEYCLOAK_FRONTEND_PORT &

echo "--------------------------------------"
echo "| Step 2: Wait for Keycloak to start |"
echo "--------------------------------------"

if [[ -z "${KEYCLOAK_SERVER_URL}" ]]; then
    echo "Skipping Keycloak Setup: Must provide KEYCLOAK_SERVER_URL in environment"
    return 0
fi

until curl ${KEYCLOAK_SERVER_URL} -sf -o /dev/null;
do
  echo $(date) " Still waiting for Keycloak to start..."
  sleep 5
done

echo "---------------------"
echo "| Step 3: Configure |"
echo "---------------------"
/scripts/setup.sh

echo "----------"
echo "| READY! |"
echo "----------"

sleep infinity