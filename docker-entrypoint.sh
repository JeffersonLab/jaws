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
/scripts/broker/create-topics.py


echo "---------------------------------------"
echo "Step 3: Adding Schemas to the registry "
echo "---------------------------------------"
/scripts/registry/create-schemas.py


echo "-----------------------"
echo "Step 4: Adding classes "
echo "-----------------------"
if [[ -z "${ALARM_CLASSES}" ]]; then
  echo "No class definitions specified"
elif [[ -f "$ALARM_CLASSES" ]]; then
  echo "Attempting to setup class definitions from file $ALARM_CLASSES"
  /scripts/client/set-class.py --file "$ALARM_CLASSES"
else
  echo "Attempting to setup classes"
  IFS=','
  read -a definitions <<< "$ALARM_CLASSES"
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
      echo "Creating class ${name} ${location}" "${category}" "${priority}" \
          "${rationale}" "${correctiveaction}" "${pointofcontactusername}" "${screenpath}"
      /scripts/client/set-class.py "${name}" --location "${location}" --category "${category}" \
          --priority "${priority}" --rationale "${rationale}" --correctiveaction "${correctiveaction}" \
          --pointofcontactusername "${pointofcontactusername}" --screenpath "${screenpath}"
    done
fi


echo "-----------------------------------"
echo "Step 5: Adding alarm registrations "
echo "-----------------------------------"
if [[ -z "${ALARM_REGISTRATIONS}" ]]; then
  echo "No alarm definitions specified"
elif [[ -f "$ALARM_REGISTRATIONS" ]]; then
  echo "Attempting to setup alarm definitions from file $ALARM_REGISTRATIONS"
  /scripts/client/set-registration.py --file "$ALARM_REGISTRATIONS"
else
  echo "Attempting to setup registrations"
  IFS=','
  read -a definitions <<< "$ALARM_REGISTRATIONS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      pv="${def[1]}"
      location="${def[2]}"
      category="${def[3]}"
      screenpath="${def[4]}"
      echo "Creating registration ${name} ${pv} ${location}" "${category}" "${screenpath}"
      if [[ -z "${pv}" ]]; then
        /scripts/client/set-registration.py "${name}" --producersimple --location "${location}" --category "${category}" --screenpath "${screenpath}"
      else
        /scripts/client/set-registration.py "${name}" --producerpv "${pv}" --location "${location}" --category "${category}" --screenpath "${screenpath}"
      fi
    done
fi

sleep infinity
