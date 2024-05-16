#!/bin/bash

TAG=$1

DOWNLOAD_URL=https://raw.githubusercontent.com/JeffersonLab/jaws/${TAG}/jlab/compose.yaml
COMPOSE_FILE=compose.yaml
APP_HOME=/opt/jaws

deploy() {
cd /tmp
rm -rf /tmp/${COMPOSE_FILE}
wget ${DOWNLOAD_URL}
systemctl stop jaws
mv /tmp/${COMPOSE_FILE} ${APP_HOME}
systemctl start jaws
}