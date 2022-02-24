<p>
<a href="#"><img align="right" width="200" height="150" src="https://raw.githubusercontent.com/JeffersonLab/kafka-alarm-system/master/logo.png"/></a>     
</p>


# JLab Alarm Warning System (JAWS) [![Docker](https://img.shields.io/docker/v/slominskir/jaws?sort=semver&label=DockerHub)](https://hub.docker.com/r/slominskir/jaws)
> "Don't get bit!"

An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project defines Kafka topics and [AVRO](https://avro.apache.org/) schemas, ties together the message pipeline services that make up the core alarm system in a docker-compose file, and provides Python scripts for configuring and interacting with the system.  JAWS attempts to comply with [ANSI/ISA 18.2-2016](https://www.isa.org/products/ansi-isa-18-2-2016-management-of-alarm-systems-for) where appropriate.

---
- [Overview](https://github.com/JeffersonLab/jaws#overview)
- [Usage](https://github.com/JeffersonLab/jaws#usage)
  - [Quick Start with Compose](https://github.com/JeffersonLab/jaws#quick-start-with-compose)
  - [Install](https://github.com/JeffersonLab/jaws#install) 
  - [Scripts](https://github.com/JeffersonLab/jaws#scripts)
- [Configure](https://github.com/JeffersonLab/jaws#configure)
- [Build](https://github.com/JeffersonLab/jaws#build) 
- [See Also](https://github.com/JeffersonLab/jaws#see-also)
---

## Overview
The JAWS alarm system is composed primarily of two subsystems: registrations and activations.  

Registrations make up the alarm metadata (descriptions), including corrective action and rationale.  Alarm classes are persisted on the _alarm-classes_ topic and provide a set of inheritable properties for class members.  The alarm instances are maintained on the _alarm-instances_ topic.  The inventory of all possible alarms (the master alarm database) is comprised of both classes and instance.  The JAWS effective processor joins classes to instances to form effective alarm registrations on the _effective-registrations_ topic.   

Activations indicate an alarm is annunciating (active), and timely operator action is required.  Alarms are triggered active by producing messages on the _alarm-activations_ topic.  An alarm can be overridden to either suppress or incite the active state by placing a message on the _alarm-overrides_ topic.  The effective activation state considering both actual activations and overrides is calculated by JAWS from _activations_ and _overrides_ and made available on the _effective-activations_ topic. 

**Services**
- [jaws-effective-processor](https://github.com/JeffersonLab/jaws-effective-processor): Process classes and overrides and provide effective state on the _effective-registrations_, _effective-activations_, and _effective-alarms_ topics
- [jaws-admin-gui](https://github.com/JeffersonLab/jaws-admin-gui): GUI for managing alarm registrations
- [jaws-operator-gui](https://github.com/JeffersonLab/graphical-alarm-client): GUI for monitoring alarms and managing overrides

**APIs**
- [jaws-libj](https://github.com/JeffersonLab/jaws-libj): Java API library for JAWS
- [jaws-libp](https://github.com/JeffersonLab/jaws-libp): Python API library for JAWS

**Data**
- [JLab Alarms](https://github.com/JeffersonLab/alarms)

**Plugins**
- [jaws-epics2kafka](https://github.com/JeffersonLab/jaws-epics2kafka): Connects EPICS alarms to JAWS
- [registrations2epics](https://github.com/JeffersonLab/registrations2epics): Notifies epics2kafka of EPICS alarm registration updates

## Usage

### Quick Start with Compose 
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
docker exec -it jaws /scripts/client/list-activations.py --monitor
```
4. Trip an alarm  
```
docker exec jaws /scripts/client/set-activation.py alarm1
```
**Note**: The docker-compose services require significant system resources - tested with 4 CPUs and 4GB memory.

**See**: [Docker Compose Strategy](https://gist.github.com/slominskir/a7da801e8259f5974c978f9c3091d52c)

**See**: More [Usage Examples](https://github.com/JeffersonLab/jaws/wiki/Usage-Examples)

### Install
Scripts tested with Python 3.7

Generally recommended to use a Python virtual environment to avoid dependency conflicts (else a dedicated Docker container can be used).  You can use the requirements.txt file to ensure the Python module dependencies are installed:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Scripts

[Scripts Reference](https://github.com/JeffersonLab/jaws/wiki/Scripts-Reference)

 To see all options use the --help option.


## Configure
The following environment variables are required by the scripts:

| Name             | Description                                                                                                                |
|------------------|----------------------------------------------------------------------------------------------------------------------------|
| BOOTSTRAP_SERVER | Host and port pair pointing to a Kafka server to bootstrap the client connection to a Kafka Cluster; example: `kafka:9092` |
| SCHEMA_REGISTRY  | URL to Confluent Schema Registry; example: `http://registry:8081`                                                          |

The Docker container requires the script environment variables, plus can optionally handle the following environment variables as well:

| Name            | Description                                                                                                                                                                                                                                                                                                                                             |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ALARM_LOCATIONS | Path to an alarm locations file to import ([example file](https://github.com/JeffersonLab/jaws/blob/master/examples/data/locations)), else an https URL to a file, else a comma separated list of location definitions with fields separated by the pipe symbol.  Example Inline CSV: `name\|parent` |
| ALARM_CATEGORIES | Path to an alarm categories file to import ([example file](https://github.com/JeffersonLab/jaws/blob/master/examples/data/categories)), else an https URL to a file, else a comma separated list of catgory definitions with fields.  Example Inline CSV: `name` |
| ALARM_CLASSES   | Path to an alarm classes file to import ([example file](https://github.com/JeffersonLab/jaws/blob/master/examples/data/classes)), else an https URL to a file, else a comma separated list of class definitions with fields separated by the pipe symbol.  Example Inline CSV: `name\|category\|priority\|rationale\|correctiveaction\|pointofcontactusername\|latching\|filterable\|ondelayseconds\|offdelayseconds` |
| ALARM_INSTANCES | Path to an alarm instances file to import ([example file](https://github.com/JeffersonLab/jaws/blob/master/examples/data/instances)), else an https URL to a file, else a comma separated list of instance definitions with fields separated by the pipe symbol.  Leave epicspv field empty for SimpleProducer. Example Inline CSV: `name\|class\|epicspv\|location\|maskedby\|screencommand` |

## Build
This [Python 3.7](https://www.python.org/) project can be built using either the Python [virtual environment](https://docs.python.org/3/tutorial/venv.html) feature or a dedicated Docker container to isolate dependencies.   The [pip](https://pypi.org/project/pip/) tool can be used to download dependencies.  Docker was used extensively for development due to the dependency on the Kafka ecosystem, so the easiest way to build the project is with a Docker build:

```
git clone https://github.com/JeffersonLab/jaws
cd jaws
docker build .
```

**Note for JLab On-Site Users**: Jefferson Lab has an intercepting [proxy](https://gist.github.com/slominskir/92c25a033db93a90184a5994e71d0b78)

**See**: [Docker Development Quick Reference](https://gist.github.com/slominskir/a7da801e8259f5974c978f9c3091d52c#development-quick-reference)

## See Also
 - [Overrides and Effective State](https://github.com/JeffersonLab/jaws/wiki/Overrides-and-Effective-State)
 - [Software Design](https://github.com/JeffersonLab/jaws/wiki/Software-Design)
 - [Developer Notes](https://github.com/JeffersonLab/jaws/wiki/Developer-Notes)
