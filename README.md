<p>
<a href="#"><img align="right" width="200" height="150" src="https://raw.githubusercontent.com/JeffersonLab/kafka-alarm-system/master/logo.png"/></a>     
</p>


# JLab Alarm Warning System (JAWS) [![Docker](https://img.shields.io/docker/v/slominskir/jaws?sort=semver&label=DockerHub)](https://hub.docker.com/r/slominskir/jaws)
> "Don't get bit!"

An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project defines Kafka topics and schemas, ties together the message pipeline services that make up the core alarm system in a docker-compose file, and provides Python scripts for configuring and interacting with the system.  JAWS attempts to comply with [ANSI/ISA 18.2-2016](https://www.isa.org/products/ansi-isa-18-2-2016-management-of-alarm-systems-for) where appropriate.

---
- [Overview](https://github.com/JeffersonLab/jaws#overview)
- [Quick Start with Compose](https://github.com/JeffersonLab/jaws#quick-start-with-compose)
- [Scripts](https://github.com/JeffersonLab/jaws#scripts)
- [Docker](https://github.com/JeffersonLab/jaws#docker)
- [See Also](https://github.com/JeffersonLab/jaws#see-also)
---

## Overview
The JAWS alarm system is composed primarily of four subsystems: _classes_, _registrations_, _activations_, and _overrides_.   Alarm classes are persisted on the _alarm-classes_ topic and provide a set of inheritable properties for class members.  The inventory of all possible alarms is maintained by registering alarm definitions on the _alarm-registrations_ topic (the master alarm database).   Alarms are triggered active by producing messages on the _alarm-activations_ topic.     An alarm can be overridden to either suppress or incite the active state by placing a message on the _alarm-overrides_ topic.  

**Services**
- [jaws-alarm-processor](https://github.com/JeffersonLab/jaws-alarm-processor): Process classes and overrides and provide effective state on the _effective-registrations_, _effective-activations_, and _effective-alarms_ topics
- [jaws-admin-gui](https://github.com/JeffersonLab/jaws-web-admin): GUI for managing alarm registrations
- [jaws-operator-gui](https://github.com/JeffersonLab/graphical-alarm-client): GUI for monitoring alarms and managing overrides

**APIs**
- [jaws-libj](https://github.com/JeffersonLab/jaws-libj): Java API library for JAWS
- [jaws-libp](https://github.com/JeffersonLab/jaws-libp): Python API library for JAWS

**Plugins**
- [jaws-epics2kafka](https://github.com/JeffersonLab/jaws-epics2kafka): Connects EPICS alarms to JAWS

## Quick Start with Compose 
1. Grab project
```
git clone https://github.com/JeffersonLab/jaws
cd jaws
```
2. Launch Docker
```
docker-compose up
```
3. Monitor active alarms
```
docker exec -it jaws /scripts/client/list-active.py --monitor
```
4. Trip an alarm  
```
docker exec jaws /scripts/client/set-active.py alarm1
```
**Note**: The docker-compose services require significant system resources - tested with 4 CPUs and 4GB memory.

**Note**: The docker-compose up command implicitly reads both _docker-compose.yml_ and _docker-compose.override.yml_.

**See**: More [Usage Examples](https://github.com/JeffersonLab/jaws/wiki/Usage-Examples)

## Scripts

[Scripts Reference](https://github.com/JeffersonLab/jaws/wiki/Scripts-Reference)

 To see all options use the --help option.

### Python Environment
Scripts tested with Python 3.7

Generally recommended to use a Python virtual environment to avoid dependency conflicts.  You can use the requirements.txt file to ensure the Python module dependences are installed:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

*Note*: [Jefferson Lab Internal Proxy](https://gist.github.com/slominskir/92c25a033db93a90184a5994e71d0b78)

### Configure
The following environment variables are required by the scripts:

| Name | Description |
|----------|---------|
| BOOTSTRAP_SERVER | Host and port pair pointing to a Kafka server to bootstrap the client connection to a Kafka Cluser; example: `kafka:9092` |
| SCHEMA_REGISTRY | URL to Confluent Schema Registry; example: `http://registry:8081` |

## Docker
```
docker pull slominskir/jaws
```
Image hosted on [DockerHub](https://hub.docker.com/r/slominskir/jaws)

**Note**: When developing the app you can mount the build artifact into the container by substituting the docker-compose up command with:
```
docker-compose -f docker-compose.yml -f docker-compose-dev.yml up
```

## See Also
 - [Overrides and Effective State](https://github.com/JeffersonLab/jaws/wiki/Overrides-and-Effective-State)
 - [Software Design](https://github.com/JeffersonLab/jaws/wiki/Software-Design)
 - [Developer Notes](https://github.com/JeffersonLab/jaws/wiki/Developer-Notes)
