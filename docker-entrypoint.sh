#!/bin/bash

echo "------------------------------------------------------"
echo "Step 1: Waiting for Schema Registry to start listening"
echo "------------------------------------------------------"
while [ $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) -eq 000 ] ; do
  echo -e $(date) " Registry listener HTTP state: " $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) " (waiting for 200)"
  sleep 5
done

echo "---------------------------------------"
echo "Step 2: Adding Schemas to the registry "
echo "---------------------------------------"
/scripts/registry/create-alarm-schemas.py

echo "----------------------------------------------------------------"
echo "Step 3: Adding alarm definitions to the registered-alarms topic "
echo "----------------------------------------------------------------"
if [[ -z "${ALARM_DEFINITIONS}" ]]; then
  echo "No alarm definitions specified"
else
  echo "Attempting to setup alarm definitions"
  IFS=','
  read -a definitions <<< "$ALARM_DEFINITIONS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      pv="${def[1]}"
      location="${def[2]}"
      category="${def[3]}"
      screenpath="${def[4]}"
      echo "Creating alarm definition ${name} ${pv} ${location}" "${category}" "${screenpath}"
      /scripts/client/set-registered.py "${name}" --producerpv "${pv}" --location "${location}" --category "${category}" --screenpath "${screenpath}"
    done
fi

sleep infinity
