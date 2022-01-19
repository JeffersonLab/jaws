#!/bin/bash

# Set Timezone
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

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


beginswith() { case $2 in "$1"*) true;; *) false;; esac; }



echo "-------------------------"
echo "Step 4: Adding locations "
echo "-------------------------"
if [[ -z "${ALARM_LOCATIONS}" ]]; then
  echo "No locations specified"
elif beginswith 'https://' "${ALARM_LOCATIONS}"; then
  echo "HTTPS URL specified: $ALARM_LOCATIONS"
  wget -O /tmp/locations "$ALARM_LOCATIONS"
  /scripts/client/set-location.py --file /tmp/locations
elif [[ -f "$ALARM_LOCATIONS" ]]; then
  echo "Attempting to setup locations from file $ALARM_LOCATIONS"
  /scripts/client/set-location.py --file "$ALARM_LOCATIONS"
else
  echo "Attempting to setup locations"
  IFS=','
  read -a definitions <<< "$ALARM_LOCATIONS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      parent="${def[1]}"
      echo "Creating location ${name} ${parent}"
      /scripts/client/set-location.py "${name}" --parent "${parent}"
    done
fi


echo "--------------------------"
echo "Step 5: Adding categories "
echo "--------------------------"
if [[ -z "${ALARM_CATEGORIES}" ]]; then
  echo "No categories specified"
elif beginswith 'https://' "${ALARM_CATEGORIES}"; then
  echo "HTTPS URL specified: $ALARM_CATEGORIES"
  wget -O /tmp/categories "$ALARM_CATEGORIES"
  /scripts/client/set-category.py --file /tmp/categories
elif [[ -f "$ALARM_CATEGORIES" ]]; then
  echo "Attempting to setup categories from file $ALARM_CATEGORIES"
  /scripts/client/set-category.py --file "$ALARM_CATEGORIES"
else
  echo "Attempting to setup categories"
  IFS=','
  read -a definitions <<< "$ALARM_CATEGORIES"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      echo "Creating category ${name}"
      /scripts/client/set-category.py "${name}"
    done
fi


echo "-----------------------"
echo "Step 6: Adding classes "
echo "-----------------------"
if [[ -z "${ALARM_CLASSES}" ]]; then
  echo "No class definitions specified"
elif beginswith 'https://' "${ALARM_CLASSES}"; then
  echo "HTTPS URL specified: $ALARM_CLASSES"
  wget -O /tmp/classes "$ALARM_CLASSES"
  /scripts/client/set-class.py --file /tmp/classes
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
      category="${def[1]}"
      priority="${def[2]}"
      rationale="${def[3]}"
      correctiveaction="${def[4]}"
      pointofcontactusername="${def[5]}"
      latching="${def[6]}"
      filterable="${def[7]}"
      ondelayseconds="${def[8]}"
      offdelayseconds="${def[9]}"
      echo "Creating class ${name} ${category} ${priority}" \
          "${rationale}" "${correctiveaction}" "${pointofcontactusername}" "${latching}" "${filterable}" \
          "${ondelayseconds}" "${offdelayseconds}"
      /scripts/client/set-class.py "${name}" --category "${category}" \
          --priority "${priority}" --rationale "${rationale}" --correctiveaction "${correctiveaction}" \
          --pointofcontactusername "${pointofcontactusername}" --latching "${latching}" --filterable "${filterable}" \
          --ondelayseconds "${ondelayseconds}" --offdelayseconds "${offdelayseconds}"
    done
fi


echo "-------------------------"
echo "Step 7: Adding instances "
echo "-------------------------"
if [[ -z "${ALARM_INSTANCES}" ]]; then
  echo "No alarm definitions specified"
elif beginswith 'https://' "${ALARM_INSTANCES}"; then
  echo "HTTPS URL specified: $ALARM_INSTANCES"
  wget -O /tmp/instances "$ALARM_INSTANCES"
  /scripts/client/set-instance.py --file /tmp/instances
elif [[ -f "$ALARM_INSTANCES" ]]; then
  echo "Attempting to setup alarm definitions from file $ALARM_INSTANCES"
  /scripts/client/set-instance.py --file "$ALARM_INSTANCES"
else
  echo "Attempting to setup registrations"
  IFS=','
  read -a definitions <<< "$ALARM_INSTANCES"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      class="${def[1]}"
      pv="${def[2]}"
      location="${def[3]}"
      maskedby="${def[4]}"
      screencommand="${def[5]}"
      echo "Creating registration ${name} ${class} ${pv} ${location} ${category} ${screenpath}"
      if [[ -z "${pv}" ]]; then
        /scripts/client/set-instance.py "${name}" --producersimple --alarmclass "${class}" --location "${location}" \
         --maskedby "${maskedby}" --screenpath "${screenpath}"
      else
        /scripts/client/set-instance.py "${name}" --producerpv "${pv}" --alarmclass "${class}" \
         --location "${location}" --maskedby "${maskedby}" --screencommand "${screencommand}"
      fi
    done
fi

sleep infinity
