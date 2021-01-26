# kafka-alarm-system [![Docker Image Version (latest semver)](https://img.shields.io/docker/v/slominskir/kafka-alarm-system?sort=semver)](https://hub.docker.com/r/slominskir/kafka-alarm-system)
An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project defines topic schemas, ties together the message pipeline services that make up the core alarm system in a docker-compose file, and provides Python scripts for configuring and interacting with the system.  

---
- [Overview](https://github.com/JeffersonLab/kafka-alarm-system#overview)
- [Quick Start with Compose](https://github.com/JeffersonLab/kafka-alarm-system#quick-start-with-compose)
- [Topics and Schemas](https://github.com/JeffersonLab/kafka-alarm-system#topics-and-schemas)
   - [Tombstones](https://github.com/JeffersonLab/kafka-alarm-system#tombstones)
   - [Customize Alarms](https://github.com/JeffersonLab/kafka-alarm-system#customize-alarms)
     - [Active Alarm Types](https://github.com/JeffersonLab/kafka-alarm-system#active-alarm-types)
   - [Acknowledgements](https://github.com/JeffersonLab/kafka-alarm-system#acknowledgements)
   - [Headers](https://github.com/JeffersonLab/kafka-alarm-system#headers)
- [Scripts](https://github.com/JeffersonLab/kafka-alarm-system#scripts)
- [See Also](https://github.com/JeffersonLab/kafka-alarm-system#see-also)
---

## Overview
The alarm system is composed of three subsystems: registered-alarms, active-alarms, and shelved-alarms.   The inventory of all possible alarms is maintained by registering or unregistering alarm definitions on the __registered-alarms__ topic.   Alarms are triggered active and also acknowledged by producing messages on the __active-alarms__ topic.     An alarm can be shelved to deemphasize the fact it is active by placing a message on the __shelved-alarms__ topic.  The alarm system is composed of the following services:
- **Sources**
   - anything authorized to produce messages on the active-alarms topic
   - [epics2kafka](https://github.com/JeffersonLab/epics2kafka) with [kafka-transform-epics](https://github.com/JeffersonLab/kafka-transform-epics)
- **Middleware**
   - *Broker*: Kafka - distributed message system
   - *Coordinator*: [ZooKeeper](https://zookeeper.apache.org/) - required by Kafka for bookkeeping and coordination
   - *Registry*: [Confluent Schema Registry](https://github.com/confluentinc/schema-registry) - message schema lookup
   - *Utilities*: 
     - [shelved-timer](https://github.com/JeffersonLab/shelved-timer) - notifies clients of shelved alarm expiration
     - [registrations2epics](https://github.com/JeffersonLab/registrations2epics) - alarm registrations inform epics2kafka what to monitor
- **Clients**   
   - Alarm Console - defined in this project; Python CLI client
   - [Operator GUI](https://github.com/JeffersonLab/graphical-alarm-client) - a Python desktop app for operators to interface with the alarm system


**Note**: The alarm system console also contains the scripts to setup/manage the Kafka topics and their schemas needed for the alarm system.  

## Quick Start with Compose 
1. Grab project
```
git clone https://github.com/JeffersonLab/kafka-alarm-system
cd kafka-alarm-system
```
2. Launch Docker
```
docker-compose up
```
3. Monitor active alarms
```
docker exec -it console /scripts/list-active.py --monitor
```
4. Trip an alarm  
```
docker exec console /scripts/set-active-alarming.py channel1
```
**Note**: The docker-compose services require significant system resources - tested with 4 CPUs and 4GB memory.

## Topics and Schemas

The alarm system state is stored in three Kafka topics.   Topic schemas are stored in the [Schema Registry](https://github.com/confluentinc/schema-registry) in [AVRO](https://avro.apache.org/) format.  Python scripts are provided for managing the alarm system topics.  

| Topic | Description | Key Schema | Value Schema | Scripts |
|-------|-------------|------------|--------------|---------|
| registered-alarms | Set of all possible alarm metadata (descriptions). | String: alarm name | AVRO: [registered-alarms-value](https://github.com/JeffersonLab/kafka-alarm-system/blob/master/schemas/registered-alarms-value.avsc) | set-registered.py, list-registered.py |
| active-alarms | Set of alarms currently active (alarming). | AVRO: [active-alarms-key](https://github.com/JeffersonLab/kafka-alarm-system/blob/master/schemas/active-alarms-key.avsc) | AVRO: [active-alarms-value](https://github.com/JeffersonLab/kafka-alarm-system/blob/master/schemas/active-alarms-value.avsc) | set-active-alarming.py, set-active-ack.py, set-active-alarming-epics.py, set-active-ack-epics.py, list-active.py |
| shelved-alarms | Set of alarms that have been shelved. | String: alarm name | AVRO: [shelved-alarms-value](https://github.com/JeffersonLab/kafka-alarm-system/blob/master/schemas/shelved-alarms-value.avsc) | set-shelved.py, list-shelved.py |

The alarm system relies on Kafka not only for notification of changes, but for [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) - everything is stored in Kafka and the entire state of the system is built by replaying messages.   All topics have compaction enabled to remove old messages that would be overwritten on replay.  Compaction is not very aggressive though so some candidates for deletion are often lingering when clients connect so they must be prepared to handle the ordered messages on replay as ones later in the stream with the same key overwrite ones earlier.  To modify a record simply set a new one with the same key. 

### Tombstones
To unset (remove) a record write a [tombstone](https://kafka.apache.org/documentation.html#compaction) record (null/None value).  This can be done with the provided scripts using the --unset option.  The tombstone approach is used to unregister, unshelve, unacknowledge, and unset active alarming.   

### Customize Alarms
The information registered with an alarm can be customized by modifying the [registered-alarms-value.asvc](https://github.com/JeffersonLab/kafka-alarm-system/blob/master/schemas/registered-alarms-value.avsc) schema.  For example, producer, locations, and categories are domain specific.

#### Active Alarm Types
Since different alarm producers may have producer specific alarm data the active alarm schema is actually an extendable union of schemas.   Generally the basic alarming or acknowledgement messages should be used for simplicity, but sometimes extra info is required.  For example, EPICS alarms have severity and status fields.  New Active Alarm Types can be defined by creating new AVRO schema.

**Note**: It is difficult to have a single (non-union) active-alarm schema that represents all possible alarm sources and has a fixed set of fields because that requires translation from the original fields to the unified fields, and decisions about (1) what are the set of unified fields and (2) how to map data to them, may result in some information being lost in translation.   Therefore, a union of schemas is used to preserve original fields.    If desired, an opinionated custom translation layer could be added to make these decisions and consolidate the various types - for example using a Kafka Streams app.

**Note**: The schema for active-alarm-value contains a single field _msg_, which is a union of records.  The _msg_ field appears unnecessary, and as an alternative the entire value could have been a union. However, a nested union is less problematic than a union at the AVRO root ([confluent blog](https://www.confluent.io/blog/multiple-event-types-in-the-same-kafka-topic/)).   If a union was used at the root then (1) the schema must be pre-registered with the registry instead of being created on-the-fly by clients, (2) the AVRO serializer must have additional configuration:
```
auto.register.schemas=false
use.latest.version=true
```
This may appear especially odd with the basic alarming and ack types as they have no fields.   For example the value for each is:
```
{"msg":{}}
```
instead of:
```
{}
```
**Note**: EPICS active alarms and acknowledgements also have explicit NO_ALARM and NO_ACK enumerations values that are included to maintain a one-to-one mapping of EPICS field values.  This means clients must be prepared to handle EPICS message value containing tombstone and NO_ALARM (and even severity INVALID).   Generally, a tombstone will not be encountered for EPICS messages as a no record scenario happens only if an alarm has never been registered before and epics2kafka will use explicit NO_ALARM once registered. 

**Note**: Schema references are not used at this time since the number of types is small and because the [Confluent Python API does not support it](https://github.com/confluentinc/confluent-kafka-python/issues/974).   In future versions of the active-alarms-value schema references may be used instead of embedding all type schemas inside the one file.

### Acknowledgements
The alarm system supports acknowledgements - alarms that move in and out of an alarming state too quickly for users to notice can be emphasized by registering them as "latching", so they require acknowledgment.  Since acknowledgements need to be tied to a specific instance of an alarming message alarm acknowledgements are placed on the same topic as alarming messages (active-alarms) to ensure messages are ordered (on a single partition).  Since they share the active-alarms topic, acks are also typed - for example EPICS acknowledgements include severity for timing purposes - an ack on a MINOR alarm does not interfere with a new MAJOR alarm that may happen before the MINOR ack is delivered (an untyped ack could inadvertantly acknowledge a more severe alarm than was intended by the user). 

**Note**: Acknowledgements add attention to alarms that toggle active _quickly_, whereas shelving removes attention from alarms that go active _frequently_.

### Headers
The alarm system topics are expected to include audit information in Kafka message headers:

| Header | Description |
|--------|-------------|
| user | The username of the account whom produced the message |
| producer | The application name that produced the message |
| host | The hostname where the message was produced |

Additionally, the built-in timestamp provided in all Kafka messages is used to provide basic message timing information.  The alarm system uses the default producer provided timestamps (as opposed to broker provided), so timestamps may not be ordered.

**Note**: There is no schema for message headers so content is not easily enforceable.  However, the topic management scripts provided include the audit headers listed.

## Scripts

[Scripts Reference](https://github.com/JeffersonLab/kafka-alarm-system/wiki/Scripts-Reference)

 To see all options use the --help option.

### Docker
A docker image containing scripts can be built from the Dockerfile included in the project.  To build within a network using man-in-the-middle network scanning (self-signed certificate injection) you can provide an optional build argument pointing to the custom CA certificate file (pip will fail to download dependencies if certificates can't be verified).   For example:
```
docker build -t console . --build-arg CUSTOM_CRT_URL=http://pki.jlab.org/JLabCA.crt
```
Grab Image from [DockerHub](https://hub.docker.com/r/slominskir/kafka-alarm-system):
```
docker pull slominskir/kafka-alarm-system
```

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
| KAFKA_HOME | Path to Kafka installation; example: `/opt/kafka` |
| CONFLUENT_HOME | Path to Confluent ([community edition](http://packages.confluent.io/archive/6.0/confluent-community-6.0.1.zip)) installation; example: `/opt/confluent-6.0.1` |

**Note**: Confluent home is needed for scripts that operate on AVRO / Schema Registry, which Apache Kafka by itself doesn't support

## See Also
 - [Developer Notes](https://github.com/JeffersonLab/kafka-alarm-system/wiki/Developer-Notes)
