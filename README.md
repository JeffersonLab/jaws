<p>
<a href="#"><img align="right" width="200" height="150" src="https://raw.githubusercontent.com/JeffersonLab/kafka-alarm-system/master/logo.png"/></a>     
</p>


# JLab Alarm Warning System (JAWS) [![Docker Image Version (latest semver)](https://img.shields.io/docker/v/slominskir/jaws?sort=semver&label=DockerHub)](https://hub.docker.com/r/slominskir/jaws)
> "Don't get bit!"

An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project defines topic schemas, ties together the message pipeline services that make up the core alarm system in a docker-compose file, and provides Python scripts for configuring and interacting with the system.  JAWS attempts to comply with [ANSI/ISA 18.2-2016](https://www.isa.org/products/ansi-isa-18-2-2016-management-of-alarm-systems-for) where appropriate.

---
- [Overview](https://github.com/JeffersonLab/jaws#overview)
- [Quick Start with Compose](https://github.com/JeffersonLab/jaws#quick-start-with-compose)
- [Topics and Schemas](https://github.com/JeffersonLab/jaws#topics-and-schemas)
   - [Tombstones](https://github.com/JeffersonLab/jaws#tombstones)
   - [Headers](https://github.com/JeffersonLab/jaws#headers)
   - [Customize Alarms](https://github.com/JeffersonLab/jaws#customize-alarms)
- [Overrides](https://github.com/JeffersonLab/jaws#overrides)
   - [Incited Alarms](https://github.com/JeffersonLab/jaws#incited-alarms)
   - [Suppressed Alarms](https://github.com/JeffersonLab/jaws#suppressed-alarms)
- [Scripts](https://github.com/JeffersonLab/jaws#scripts)
- [Docker](https://github.com/JeffersonLab/jaws#docker)
- [See Also](https://github.com/JeffersonLab/jaws#see-also)
---

## Overview
The alarm system is composed of three subsystems: registered-alarms, active-alarms, and overridden-alarms.   The inventory of all possible alarms is maintained by registering or unregistering alarm definitions on the __registered-alarms__ topic (the master alarm database).   Alarms are triggered active by producing messages on the __active-alarms__ topic.     An alarm can be overridden to either suppress or incite the active state by placing a message on the __overridden-alarms__ topic.  The alarm system is composed of the following services:
- **Sources**
   - anything authorized to produce messages on the active-alarms topic
      - plugin: [epics2kafka-alarms](https://github.com/JeffersonLab/epics2kafka-alarms)
- **Middleware**
   - *Broker*: Kafka - distributed message system
   - *Coordinator*: [ZooKeeper](https://zookeeper.apache.org/) - required by Kafka for bookkeeping and coordination
   - *Registry*: [Confluent Schema Registry](https://github.com/confluentinc/schema-registry) - message schema lookup
   - *Utilities*: 
     - [shelved-timer](https://github.com/JeffersonLab/shelved-timer) - notifies clients of shelved alarm expiration
     - [alarms-filter](https://github.com/JeffersonLab/alarms-filter) - provides shared filtered active-alarms topics (suppresses alarms)
     - plugin: [registrations2epics](https://github.com/JeffersonLab/registrations2epics) - alarm registrations inform epics2kafka what to monitor
- **Clients**   
   - Admin Command Line Interface (CLI) - Python scripts included in this project to manage the alarm system
   - [Operator Graphical User Interface (GUI)](https://github.com/JeffersonLab/graphical-alarm-client) - Python desktop app for operators to interface with the alarm system


**Note**: The admin CLI scritps are used to:
   1. Setup/manage the Kafka topics
   2. Setup/manage AVRO schemas in the registry
   3. Produce and consume alarm system messages

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
docker exec jaws /scripts/client/set-alarming.py alarm1
```
**Note**: The docker-compose services require significant system resources - tested with 4 CPUs and 4GB memory.

## Topics and Schemas

The alarm system state is stored in three Kafka topics.   Topic schemas are stored in the [Schema Registry](https://github.com/confluentinc/schema-registry) in [AVRO](https://avro.apache.org/) format.  Python scripts are provided for managing the alarm system topics.  

| Topic | Description | Key Schema | Value Schema | Scripts |
|-------|-------------|------------|--------------|---------|
| registered-alarms | Set of all possible alarm metadata (descriptions). | String: alarm name | AVRO: [registered-alarms-value](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/registered-alarms-value.avsc) | set-registered.py, list-registered.py |
| active-alarms | Set of alarms currently active (alarming). | AVRO: [active-alarms-key](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/active-alarms-key.avsc) | AVRO: [active-alarms-value](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/active-alarms-value.avsc) | set-alarming.py, set-ack.py, list-active.py |
| overridden-alarms | Set of alarms that have been overridden. | AVRO: [overridden-alarms-key](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/overridden-alarms-key.avsc) | AVRO: [overridden-alarms-value](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/overridden-alarms-value.avsc) | set-overridden.py, list-overridden.py |

The alarm system relies on Kafka not only for notification of changes, but for [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) - everything is stored in Kafka and the entire state of the system is built by replaying messages.   All topics have compaction enabled to remove old messages that would be overwritten on replay.  Compaction is not very aggressive though so some candidates for deletion are often lingering when clients connect so they must be prepared to handle the ordered messages on replay as ones later in the stream with the same key overwrite ones earlier.  To modify a record simply set a new one with the same key. 

### Tombstones
To unset (remove) a record write a [tombstone](https://kafka.apache.org/documentation.html#compaction) record (null/None value).  This can be done with the provided scripts using the --unset option.  The tombstone approach is used to unregister, unsuppress, unacknowledge, and unset active alarming.   

### Headers
The alarm system topics are expected to include audit information in Kafka message headers:

| Header | Description |
|--------|-------------|
| user | The username of the account whom produced the message |
| producer | The application name that produced the message |
| host | The hostname where the message was produced |

Additionally, the built-in timestamp provided in all Kafka messages is used to provide basic message timing information.  The alarm system uses the default producer provided timestamps (as opposed to broker provided), so timestamps may not be ordered.

**Note**: There is no schema for message headers so content is not easily enforceable.  However, the topic management scripts provided include the audit headers listed.

### Schema Peculiarities

#### AVRO Unions
For AVRO Unions we avoid placing this structure at the root.  Instead we use a single field _msg_, which is a union of records.  The _msg_ field appears unnecessary, and as an alternative the entire value could have been a union. However, a nested union is less problematic than a union at the AVRO root ([confluent blog](https://www.confluent.io/blog/multiple-event-types-in-the-same-kafka-topic/)).   If a union was used at the root then (1) the schema must be pre-registered with the registry instead of being created on-the-fly by clients, (2) the AVRO serializer must have additional configuration:
```
auto.register.schemas=false
use.latest.version=true
```
This may appear especially odd with messages that have no fields.   For example the value is:
```
{"msg":{}}
```
instead of:
```
{}
```
#### Schema References
Schema references are not used at this time since the number of types is small, but mainly because the [Confluent Python API does not support it](https://github.com/confluentinc/confluent-kafka-python/issues/974).   In future versions schema references may be used instead of embedding multiple type schemas inside files.

### Customize Alarms
The information registered with an alarm can be customized by modifying the [registered-alarms-value](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/registered-alarms-value.avsc) schema.  For example, producer, locations, and categories are domain specific.

Overrides can be customized by modifiying the [overridden-alarms-key](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/overridden-alarms-key.avsc) and [overridden-alarms-value](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/overridden-alarms-value.avsc) schemas.  For example, to add or remove override options.

Generally alarm producers should simply indicate that an alarm is active or not.   However, not all producers work this way - some are a tangled mess (like EPICS, which indicates priority and type at the time of activation notification - a single EPICS PV therefore maps to multiple alarms).   It is possible to modify the [active-alarms-key](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/active-alarms-key.avsc) and [active-alarms-value](https://github.com/JeffersonLab/jaws/blob/master/config/subject-schemas/active-alarms-value.avsc) schemas to be anything you want.  You can even make the schema a union of producer specific schemas (we did this initially).  However, we've ultimtely decided at JLab to use a simpler approach and use an active-alarms schema with key alarm name and value contains an optional String extra info field.  In the case of EPICS we have a Kafka Streams app that maps the on-the-fly active messages containing priority and type to specific registered alarms (in the works!).

## Overrides

![Active Alarm Message Flow](https://github.com/JeffersonLab/jaws/raw/master/docs/ActiveAlarmFlowDiagram.png?raw=true "Active Alarm Message Flow")

Operator Initiated
  - Disable and  Undisable
  - Shelve and Unshelve 
  - Filter and Unfilter 
  - Unlatch (acknowledge)

Automated
 - On-Delay and Un-On-Delay
 - Off-Delay† and Un-Off-Delay
 - Latch† (unacknowledged)
 - Mask and Unmask
 - Unshelve (timer expiration or one-shot active encountered)

_† Incited alarm override (Others are suppressed override)_

### Incited Alarms
The alarm system supports two types of alarm incitement: latching and off-delays.   Latching is for alarms that move in and out of an alarming state too quickly for operators to notice and can be emphasized by registering them as "latching", so they require acknowledgment.  The Automated Override Processor adds a latch record to the overridden-alarms topic each time an alarm becomes active.  An operator must then unlatch the alarm by producing an acknowledement message on the overridden-alarms topic.  Off delays extend the effective active state of an alarm and is configured in the registered-alarms topic.  the Automated Override Processor monitors the active-alarms topic and adds an off-delay to the overriden-alarms topic once the alarm first becomes active and removed automatically once expired. 

### Suppressed Alarms
An alarm can be suppressed via multiple means simultaneously, but suppression precedence determines the effective suppression state:

**Alarm Suppression States**     

| Precedence | Name | Duration | Definition |
|---|---|---|---|
| 1 | Disabled | Indefinite | A broken alarm can be flagged as out-of-service |
| 2 | Filtered | Indefinite | An alarm can be "suppressed by design" - generally a group of alarms are filtered out when not needed for the current machine program  |
| 3 | Masked | Only while parent alarm is active | An alarm can be suppressed by a parent alarm to minimize confusion during an alarm flood and build an alarm hierarchy |
| 4 | Delayed | Short with expiration | An alarm with an on-delay is temporarily suppressed to minimize fleeting/chattering |  
| 5 | Shelved | Short with expiration | A nuisance alarm can be temporarily shelved with a short expiration date |

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

## See Also
 - [Developer Notes](https://github.com/JeffersonLab/jaws/wiki/Developer-Notes)
