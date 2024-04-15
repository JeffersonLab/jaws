<p>
<a href="#"><img align="right" width="100" height="75" src="https://raw.githubusercontent.com/JeffersonLab/jaws/main/logo.png"/></a>     
</p>


# JLab Alarm Warning System (JAWS)
> "Don't get bit!"

An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project integrates all the services that make up JAWS via Docker Compose.  JAWS attempts to comply with [ANSI/ISA 18.2-2016](https://www.isa.org/products/ansi-isa-18-2-2016-management-of-alarm-systems-for) where appropriate.

---
- [Overview](https://github.com/JeffersonLab/jaws#overview)
- [Quick Start with Compose](https://github.com/JeffersonLab/jaws#quick-start-with-compose)
- [Install](https://github.com/JeffersonLab/jaws#install)
- [See Also](https://github.com/JeffersonLab/jaws#see-also)
---

## Overview
The JAWS alarm system is composed primarily of two subsystems: registrations and notifications.  

The inventory of all possible alarms (the master alarm database) is stored in Kafka as alarm instances, and these instances are organized into classes so that some properties are provided by their assigned alarm class.  The alarm instances are maintained on the _alarm-instances_ topic.  Alarm classes define group-shared properties such as corrective action and rationale and are persisted on the _alarm-classes_ topic.   The JAWS effective processor joins classes to instances to form effective alarm registrations on the _effective-registrations_ topic.   

Activations indicate an alarm is annunciating (active), and timely operator action is required.  Alarms are triggered active by producing messages on the _alarm-activations_ topic.  An alarm can be overridden to either suppress or incite the active state by placing a message on the _alarm-overrides_ topic.  The effective notification state considering both activations and overrides is calculated by JAWS from _activations_ and _overrides_ and made available on the _effective-notifications_ topic. 

Both effective registrations and effective notifications are combined by the JAWS effective processor on the _effective-alarms_ topic.

**Apps**
- [jaws-effective-processor](https://github.com/JeffersonLab/jaws-effective-processor): Process classes and overrides and provide effective state on the _effective-registrations_, _effective-notifications_, and _effective-alarms_ topics
- [jaws-admin-gui](https://github.com/JeffersonLab/jaws-admin-gui): GUI for managing alarm registrations
- [jaws-operator-gui](https://github.com/JeffersonLab/graphical-alarm-client): GUI for monitoring alarms and managing overrides

**APIs**
- [jaws-libj](https://github.com/JeffersonLab/jaws-libj): Java API library for JAWS
- [jaws-libp](https://github.com/JeffersonLab/jaws-libp): Python API library for JAWS including Kafka topic and Registry schema setup

**Data**
- [JLab Alarms](https://github.com/JeffersonLab/alarms)

**Extensions**
- [jaws-epics2kafka](https://github.com/JeffersonLab/jaws-epics2kafka): Connects EPICS alarms to JAWS
- [jaws-registrations2epics](https://github.com/JeffersonLab/jaws-registrations2epics): Notifies epics2kafka of EPICS alarm registration updates

## Quick Start with Compose 
1. Grab project
```
git clone https://github.com/JeffersonLab/jaws
cd jaws
```
2. Launch [Compose](https://github.com/docker/compose)
```
docker compose up
```
3. Monitor active alarms
```
docker exec -it jaws list_activations --monitor
```
4. Trip an alarm  
```
docker exec jaws set_activation alarm1
```
**Note**: The docker-compose services require significant system resources - tested with 4 CPUs and 4GB memory.

**See**: More [Usage Examples](https://github.com/JeffersonLab/jaws/wiki/Usage-Examples)

## Install
The entire JAWS application consists of multiple microservices and each one has a separate installation.  However, you can install and launch them all using the docker compose [here](https://github.com/JeffersonLab/jaws/blob/main/examples/compose/all.yml).   This Docker Compose file (and it's references) answers the question of which version of each microservice to use.   In a production environment you'll likely want to use some orchestration tooling, which could be anything from bash scripts to Compose/Ansible/Chef/Puppet/Whatever, or perhaps Kubernetes + tooling.  JLab is currently using Docker Compose on a beefy VM and the entire system is ephemeral, loading it's data from the [alarms](https://github.com/JeffersonLab/alarms) GitHub repo.  The system can be upgraded and restarted in seconds. See [internal docs](https://accwiki.acc.jlab.org/do/view/SysAdmin/JAWS).

## See Also
 - [Overrides and Effective State](https://github.com/JeffersonLab/jaws/wiki/Overrides-and-Effective-State)
 - [Software Design](https://github.com/JeffersonLab/jaws/wiki/Software-Design)
 - [Developer Notes](https://github.com/JeffersonLab/jaws/wiki/Developer-Notes)
