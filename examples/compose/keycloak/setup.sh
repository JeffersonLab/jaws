#!/bin/bash

if [[ -z "${KEYCLOAK_HOME}" ]]; then
    echo "Skipping Keycloak Setup: Must provide KEYCLOAK_HOME in environment"
    return 0
fi

if [[ -z "${KEYCLOAK_SERVER_URL}" ]]; then
    echo "Skipping Keycloak Setup: Must provide KEYCLOAK_SERVER_URL in environment"
    return 0
fi

if [[ -z "${KEYCLOAK_ADMIN}" ]]; then
    echo "Skipping Keycloak Setup: Must provide KEYCLOAK_ADMIN in environment"
    return 0
fi

if [[ -z "${KEYCLOAK_ADMIN_PASSWORD}" ]]; then
    echo "Skipping Keycloak Setup: Must provide KEYCLOAK_ADMIN_PASSWORD in environment"
    return 0
fi

if [[ -z "${KEYCLOAK_REALM}" ]]; then
    echo "Skipping Keycloak Setup: Must provide KEYCLOAK_REALM in environment"
    return 0
fi

if [[ -z "${KEYCLOAK_RESOURCE}" ]]; then
    echo "Skipping Keycloak Setup: Must provide KEYCLOAK_RESOURCE in environment"
    return 0
fi

if [[ -z "${KEYCLOAK_SECRET}" ]]; then
    echo "Skipping Keycloak Setup: Must provide KEYCLOAK_SECRET in environment"
    return 0
fi

echo "-----------------"
echo "| Step A: Login |"
echo "-----------------"
${KEYCLOAK_HOME}/bin/kcadm.sh config credentials --server "${KEYCLOAK_SERVER_URL}" --realm master --user "${KEYCLOAK_ADMIN}" --password "${KEYCLOAK_ADMIN_PASSWORD}"

echo "------------------------"
echo "| Step B: Create Realm |"
echo "------------------------"
${KEYCLOAK_HOME}/bin/kcadm.sh create realms -s realm="${KEYCLOAK_REALM}" -s enabled=true -o

echo "------------------------"
echo "| Step C: Create Roles |"
echo "------------------------"
${KEYCLOAK_HOME}/bin/kcadm.sh create roles -r "${KEYCLOAK_REALM}" -s name=${KEYCLOAK_RESOURCE}-user
${KEYCLOAK_HOME}/bin/kcadm.sh create roles -r "${KEYCLOAK_REALM}" -s name=${KEYCLOAK_RESOURCE}-admin

echo "-------------------------"
echo "| Step D: Create Client |"
echo "-------------------------"
${KEYCLOAK_HOME}/bin/kcadm.sh create clients -r "${KEYCLOAK_REALM}" -s clientId=${KEYCLOAK_RESOURCE} -s 'redirectUris=["https://localhost:8443/'${KEYCLOAK_RESOURCE}'/*"]' -s secret=${KEYCLOAK_SECRET} -s 'serviceAccountsEnabled=true'
${KEYCLOAK_HOME}/bin/kcadm.sh add-roles -r "${KEYCLOAK_REALM}" --uusername service-account-${KEYCLOAK_RESOURCE} --cclientid realm-management --rolename view-users
${KEYCLOAK_HOME}/bin/kcadm.sh add-roles -r "${KEYCLOAK_REALM}" --uusername service-account-${KEYCLOAK_RESOURCE} --cclientid realm-management --rolename view-authorization
${KEYCLOAK_HOME}/bin/kcadm.sh add-roles -r "${KEYCLOAK_REALM}" --uusername service-account-${KEYCLOAK_RESOURCE} --cclientid realm-management --rolename view-realm

echo "------------------------"
echo "| Step E: Create Users |"
echo "------------------------"
${KEYCLOAK_HOME}/bin/kcadm.sh create users -r "${KEYCLOAK_REALM}" -s username=jadams -s firstName=Jane -s lastName=Adams -s email=jadams@example.com -s enabled=true
${KEYCLOAK_HOME}/bin/kcadm.sh set-password -r "${KEYCLOAK_REALM}" --username jadams --new-password password
${KEYCLOAK_HOME}/bin/kcadm.sh add-roles -r "${KEYCLOAK_REALM}" --uusername jadams --rolename ${KEYCLOAK_RESOURCE}-user

${KEYCLOAK_HOME}/bin/kcadm.sh create users -r "${KEYCLOAK_REALM}" -s username=jsmith -s firstName=John -s lastName=Smith -s email=jsmith@example.com -s enabled=true
${KEYCLOAK_HOME}/bin/kcadm.sh set-password -r "${KEYCLOAK_REALM}" --username jsmith --new-password password
${KEYCLOAK_HOME}/bin/kcadm.sh add-roles -r "${KEYCLOAK_REALM}" --uusername jsmith --rolename ${KEYCLOAK_RESOURCE}-user

${KEYCLOAK_HOME}/bin/kcadm.sh create users -r "${KEYCLOAK_REALM}" -s username=tbrown -s firstName=Tom -s lastName=Brown -s email=tbrown@example.com -s enabled=true
${KEYCLOAK_HOME}/bin/kcadm.sh set-password -r "${KEYCLOAK_REALM}" --username tbrown --new-password password
${KEYCLOAK_HOME}/bin/kcadm.sh add-roles -r "${KEYCLOAK_REALM}" --uusername tbrown --rolename ${KEYCLOAK_RESOURCE}-user
${KEYCLOAK_HOME}/bin/kcadm.sh add-roles -r "${KEYCLOAK_REALM}" --uusername tbrown --rolename ${KEYCLOAK_RESOURCE}-admin