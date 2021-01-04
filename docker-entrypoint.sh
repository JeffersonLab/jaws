#!/bin/bash

echo "------------------------------------------------------"
echo "Step 1: Waiting for Schema Registry to start listening"
echo "------------------------------------------------------"
while [ $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) -eq 000 ] ; do
  echo -e $(date) " Registry listener HTTP state: " $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) " (waiting for 200)"
  sleep 5
done

echo "--------------------------------"
echo "Step 2: Configuring alarm topic "
echo "--------------------------------"
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
      docurl="${def[4]}"
      edmpath="${def[5]}"
      echo "Creating alarm definition ${name} ${pv} ${location}" "${category}" "${docurl}" "${edmpath}"
      /scripts/set-registered.py "${name}" --producerpv "${pv}" --location "${location}" --category "${category}" --docurl "${docurl}" --edmpath "${edmpath}"
    done
fi

sleep infinity
