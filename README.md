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
- [Release](https://github.com/JeffersonLab/jaws#release) 
- [Deploy](https://github.com/JeffersonLab/jaws#deploy) 
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
The core JAWS application consists of a set of containerized microservices which can be launched with a container orchestration tool such as Docker Compose.  The following microservices are internal to JAWS:
- Kafka
- Schema Registry
- Effective Processor
- Shell Admin Console

Optionally, the following extra containerized services are available:
- Web Admin Console
- JAWS EPICS Services

There are external services required to be available for the Admin Console and EPICS Services that can be optionally containerized as well, but at JLab we use separately managed shared instances.   You can launch a fully containerized version of JAWS which includes containerized external dependencies in the [web admin project](https://github.com/jeffersonlab/jaws-admin-gui) and [epics2kafka project](https://github.com/jeffersonlab/jaws-epics2kafka).  These external services include:
- Keycloak
- Oracle RDMS
- EPICS IOCs

The core JAWS system supports import and export of data from files.   The optional Web Admin Console adds support for loading and saving from an Oracle database.
  
## Release
The versioned artifact of this project is a set of Docker Compose files which answer the question of which version of each microservice to use together.

 - [Core compose.yaml](https://raw.githubusercontent.com/JeffersonLab/jaws/main/compose.yaml)
 - [JLab compose.yaml](https://raw.githubusercontent.com/JeffersonLab/jaws/main/jlab/compose.yaml)

**Note**: You can fetch a specific tagged version by replacing `main` with a semver tag in the URLs above.

## Deploy
At JLab we use Docker Compose.

See: [internal docs](https://accwiki.acc.jlab.org/do/view/SysAdmin/JAWS).

## See Also
 - [Overrides and Effective State](https://github.com/JeffersonLab/jaws/wiki/Overrides-and-Effective-State)
 - [Software Design](https://github.com/JeffersonLab/jaws/wiki/Software-Design)
 - [Developer Notes](https://github.com/JeffersonLab/jaws/wiki/Developer-Notes)
