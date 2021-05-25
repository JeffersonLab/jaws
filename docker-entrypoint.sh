#!/bin/bash

echo "-------------------------------------------------------"
echo "Step 1: Waiting for Schema Registry to start listening "
echo "-------------------------------------------------------"
while [ $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) -eq 000 ] ; do
  echo -e $(date) " Registry listener HTTP state: " $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) " (waiting for 200)"
  sleep 5
done


echo "------------------------"
echo "Step 2: Creating Topics "
echo "------------------------"
/scripts/broker/create-alarm-topics.py


echo "---------------------------------------"
echo "Step 3: Adding Schemas to the registry "
echo "---------------------------------------"
/scripts/registry/create-alarm-schemas.py


echo "-----------------------------------------------------------------"
echo "Step 4: Adding class definitions to the registered-classes topic "
echo "-----------------------------------------------------------------"
if [[ -z "${CLASS_DEFINITIONS}" ]]; then
  echo "No class definitions specified"
elif [[ -f "$CLASS_DEFINITIONS" ]]; then
  echo "Attempting to setup class definitions from file $CLASS_DEFINITIONS"
  /scripts/client/set-registered.py --editclass --file "$CLASS_DEFINITIONS"
else
  echo "Attempting to setup class definitions"
  IFS=','
  read -a definitions <<< "$CLASS_DEFINITIONS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      location="${def[1]}"
      category="${def[2]}"
      priority="${def[3]}"
      rationale="${def[4]}"
      correctiveaction="${def[5]}"
      pointofcontactusername="${def[6]}"
      screenpath="${def[7]}"
      echo "Creating class definition ${name} ${location}" "${category}" "${priority}" \
          "${rationale}" "${correctiveaction}" "${pointofcontactusername}" "${screenpath}"
      /scripts/client/set-registered.py --editclass "${name}" --location "${location}" --category "${category}" \
          --priority "${priority}" --rationale "${rationale}" --correctiveaction "${correctiveaction}" \
          --pointofcontactusername "${pointofcontactusername}" --screenpath "${screenpath}"
    done
fi


echo "----------------------------------------------------------------"
echo "Step 5: Adding alarm definitions to the registered-alarms topic "
echo "----------------------------------------------------------------"
if [[ -z "${ALARM_DEFINITIONS}" ]]; then
  echo "No alarm definitions specified"
elif [[ -f "$ALARM_DEFINITIONS" ]]; then
  echo "Attempting to setup alarm definitions from file $ALARM_DEFINITIONS"
  /scripts/client/set-registered.py --file "$ALARM_DEFINITIONS"
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
