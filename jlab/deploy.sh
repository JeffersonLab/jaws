#!/bin/bash

TAG=$1
APP_HOME=/opt/jaws

deploy() {
cd /tmp
rm -rf /tmp/jaws
git clone --depth 1 --branch ${TAG} https://github.com/jeffersonlab/jaws
systemctl stop jaws
mv /tmp/jaws/core.yaml ${APP_HOME}
mv /tmp/jaws/jlab.yaml ${APP_HOME}
mv /tmp/jaws/epics.yaml ${APP_HOME}
mv /tmp/jaws/web.yaml ${APP_HOME}
mv /tmp/jaws/service-versions.env ${APP_HOME}
mv /tmp/jaws/jaws-version.env ${APP_HOME}
systemctl start jaws
}