<p>
<a href="#"><img align="right" width="200" height="150" src="https://raw.githubusercontent.com/JeffersonLab/kafka-alarm-system/master/logo.png"/></a>     
</p>


# JLab Alarm Warning System (JAWS) [![Docker](https://img.shields.io/docker/v/slominskir/jaws?sort=semver&label=DockerHub)](https://hub.docker.com/r/slominskir/jaws)
> "Don't get bit!"

An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project defines topic schemas, ties together the message pipeline services that make up the core alarm system in a docker-compose file, and provides Python scripts for configuring and interacting with the system.  JAWS attempts to comply with [ANSI/ISA 18.2-2016](https://www.isa.org/products/ansi-isa-18-2-2016-management-of-alarm-systems-for) where appropriate.

---
- [Overview](https://github.com/JeffersonLab/jaws#overview)
- [Quick Start with Compose](https://github.com/JeffersonLab/jaws#quick-start-with-compose)
- [Topics and Schemas](https://github.com/JeffersonLab/jaws#topics-and-schemas)
   - [Supporting Topics and Schemas](https://github.com/JeffersonLab/jaws#supporting-topics-and-schemas)
   - [Tombstones](https://github.com/JeffersonLab/jaws#tombstones)
   - [Headers](https://github.com/JeffersonLab/jaws#headers)
   - [Customize Alarms](https://github.com/JeffersonLab/jaws#customize-alarms)
- [Overrides](https://github.com/JeffersonLab/jaws#overrides)
   - [Incited Alarms](https://github.com/JeffersonLab/jaws#incited-alarms)
   - [Suppressed Alarms](https://github.com/JeffersonLab/jaws#suppressed-alarms)
- [Alarm States](https://github.com/JeffersonLab/jaws#alarm-states) 
- [Scripts](https://github.com/JeffersonLab/jaws#scripts)
- [Docker](https://github.com/JeffersonLab/jaws#docker)
- [See Also](https://github.com/JeffersonLab/jaws#see-also)
---

## Overview
The JAWS alarm system is composed of three subsystems: _registered-alarms_, _active-alarms_, and _overridden-alarms_.   The inventory of all possible alarms is maintained by registering or unregistering alarm definitions on the _registered-alarms_ topic (the master alarm database).   Alarms are triggered active by producing messages on the _active-alarms_ topic.     An alarm can be overridden to either suppress or incite the active state by placing a message on the _overridden-alarms_ topic.  The alarm system is composed of the following services:
- **Sources**
   - anything authorized to produce messages on the _active-alarms_ topic
      - plugin: [epics2kafka-alarms](https://github.com/JeffersonLab/epics2kafka-alarms)
- **Middleware**
   - *Broker*: Kafka - distributed message system
   - *Coordinator*: [ZooKeeper](https://zookeeper.apache.org/) - required by Kafka for bookkeeping and coordination
   - *Registry*: [Confluent Schema Registry](https://github.com/confluentinc/schema-registry) - message schema lookup
   - *Stream Processors*: 
     - [alarm-state-processor](https://github.com/JeffersonLab/alarm-state-processor) - Compute alarm state given _registered-alarms_, _active-alarms_, and _overridden-alarms_ and output to the _alarm-state_ topic 
     - [alarm-auto-override-processor](https://github.com/JeffersonLab/shelved-timer) - Applys and maintains automated overrides based on configuration without manual operator intervention
     - [alarm-filter-processor](https://github.com/JeffersonLab/alarms-filter) - Applys and maintains filter commands in the generation of alarm overrides
     - plugin: [registrations2epics](https://github.com/JeffersonLab/registrations2epics) - alarm registrations inform epics2kafka what to monitor
- **Clients**   
   - Admin Command Line Interface (CLI) - Python scripts included in this project to manage the alarm system
   - [Operator Graphical User Interface (GUI)](https://github.com/JeffersonLab/graphical-alarm-client) - Python desktop app for operators to interface with the alarm system


**Note**: The admin CLI scritps are used to:
   1. Setup/manage the Kafka topics
   2. Setup/manage AVRO schemas in the registry
   3. Produce and consume alarm system messages

### JAWS APIs
 - [jaws-libj (Java)](https://github.com/JeffersonLab/jaws-libj)
 - [jaws-libp (Python)](https://github.com/JeffersonLab/jaws-libp)  

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

See: More [Usage Examples](https://github.com/JeffersonLab/jaws/wiki/Usage-Examples)

## Topics and Schemas

The alarm system state is stored in three Kafka topics.   Topic schemas are stored in the [Schema Registry](https://github.com/confluentinc/schema-registry) in [AVRO](https://avro.apache.org/) format.  Python scripts are provided for managing the alarm system topics.  

| Topic | Description | Key Schema | Value Schema | Scripts |
|-------|-------------|------------|--------------|---------|
| registered-alarms | Set of all possible alarm metadata (descriptions). | String: alarm name | AVRO: [registered-alarms-value](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/registered-alarms-value.avsc) | set-registered.py, list-registered.py |
| active-alarms | Set of alarms currently active (alarming). | String: alarm name | AVRO: [active-alarms-value](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/active-alarms-value.avsc) | set-active.py, list-active.py |
| overridden-alarms | Set of alarms that have been overridden. | AVRO: [overridden-alarms-key](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/overridden-alarms-key.avsc) | AVRO: [overridden-alarms-value](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/overridden-alarms-value.avsc) | set-overridden.py, list-overridden.py |

The alarm system relies on Kafka not only for notification of changes, but for [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) - everything is stored in Kafka and the entire state of the system is built by replaying messages.   All topics have compaction enabled to remove old messages that would be overwritten on replay.  Compaction is not very aggressive though so some candidates for deletion are often lingering when clients connect so they must be prepared to handle the ordered messages on replay as ones later in the stream with the same key overwrite ones earlier.  To modify a record simply set a new one with the same key. 

### Supporting Topics and Schemas
In addition to the three core topics, the following topics provide value add via various supporting apps:

| Topic | Description | Key Schema | Value Schema | Note |
|-------|-------------|------------|--------------|------|
| alarm-state | Contains effective alarm state considering overrides | String: alarm name | String: [alarm state](https://github.com/JeffersonLab/jaws#alarm-states) | Technically each client could figure out the alarm state themselves, but it's a chore so its done by the [alarm-state-processor](https://github.com/JeffersonLab/alarm-state-processor) |
| registered-class | Contains class-wide registration information to avoid redundant specification | AVRO: [registered-class-key](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/registered-class-key.avsc) | AVRO: [registered-class-value](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/registered-class-value.avsc) | Optionally some registration fields can be left empty and instead inherit values from a class specification - for example the corrective action for a certain class of machine Magnets (of which there are hundreds of instances) is typically the same. |
| jaws-config | Contains shared configuration data | String: config property name | String: config property value |  |

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
Schema references are being used experimentally at this time.  See: [Confluent Python API does not support schema references](https://github.com/confluentinc/confluent-kafka-python/issues/974).

### Customize Alarms
The information registered with an alarm can be customized by modifying the [registered-alarms-value](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/registered-alarms-value.avsc) schema.  For example, producer, locations, and categories are domain specific.

Overrides can be customized by modifiying the [overridden-alarms-key](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/overridden-alarms-key.avsc) and [overridden-alarms-value](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/overridden-alarms-value.avsc) schemas.  For example, to add or remove override options.

Generally alarm producers should simply indicate that an alarm is active or not.   However, not all producers work this way - some are a tangled mess (like EPICS, which indicates priority and type at the time of activation notification - a single EPICS PV therefore maps to multiple alarms).   It is possible to modify the [active-alarms-value](https://github.com/JeffersonLab/jaws-libp/blob/main/src/jlab_jaws/avro/subject_schemas/active-alarms-value.avsc) schemas to be anything you want.  The schema is currently a union of schemas for flexibility:

 - **SimpleAlarming**: Alarming state for a simple alarm, if record is present then alarming, if missing/tombstone then not.  There are no fields. 
 - **NoteAlarming**: Alarming state for an alarm with an extra information string. 
 - **EPICSAlarming**: Alarming state for an EPICS alarm with STAT and SEVR fields.

At JLab we we're expermimenting with various strategies such as translating EPICSAlarming records (raw EPICS records) into NoteAlarming records using a Kafka Streams app that maps the on-the-fly active messages containing SEVR to one of two specific registered alarms (PV Name + MAJOR, PV Name + MINOR) and then stashing the dubiously valued STAT field as a note.

## Overrides
An alarm can be in two basic states: 
  - "Active": Timely operator action required (actively alarming)
  - "Normal": No operator action required

In an ideal world alarm producers are sophisticated and aware of the machine program and nuisance alarms are non-existant.  Nuisance alarms are alarms which are in the Active state incorrectly - there really isn't any operator action required despite the alarm producer indicating there is.   In practice, nuisance alarms are very common and quickly undermine the value of an alarm system.   Overrides are one way for operators to deal with nuisance alarms by adding a layer of indirection from alarm producers and allowing effective alarm state to differ from actual alarm state.

![Active Alarm Message Flow](https://github.com/JeffersonLab/jaws/raw/master/docs/ActiveAlarmFlowDiagram.png?raw=true "Active Alarm Message Flow")

Operator Initiated
  - Disable and  Undisable
  - Shelve and Unshelve 
  - Filter and Unfilter 
  - Unlatch (acknowledge)

Automated
 - On-Delay and Un-On-Delay
 - Off-Delay† and Un-Off-Delay
 - Latch† (unacknowledge)
 - Mask and Unmask
 - Unshelve (timer expiration or one-shot active encountered)

_† Incited alarm override (Others are suppressed override)_

### Incited Alarms
The alarm system supports two types of alarm incitement: latching and off-delays.   Latching is for alarms that move in and out of an alarming state too quickly for operators to notice and can be emphasized by registering them as "latching", so they require acknowledgment.  The Automated Override Processor adds a latch record to the overridden-alarms topic each time an alarm becomes active.  An operator must then unlatch the alarm by producing an acknowledement message on the overridden-alarms topic.  Off delays extend the effective active state of an alarm and is configured in the registered-alarms topic.  The Automated Override Processor monitors the active-alarms topic and adds an off-delay to the overriden-alarms topic once an alarm first becomes active and removes the override automatically once expired. 

### Suppressed Alarms
An alarm can be suppressed, which means should be treated as Normal (no action required) regardless if actually active or not.

### Override Precedence     

Multiple overrides are possible simultaneously and precedence determines effective override state, which is factored into effective alarm state.

| Precedence | Name | Trigger | Duration | Note |
|---|---|---|---|----|
| 1 | Disabled | Manual Operator Command | Indefinite | A broken alarm can be flagged as out-of-service |
| 2 | Filtered | Manual Operator Command of filterable alarm | Indefinite | An alarm can be "suppressed by design" - generally a group of alarms are filtered out when not needed for the current machine program.  The Filter Processor helps operators filter multiple alarms with simple grouping commands (like by area).  |
| 3 | Masked | Automatic upon activtation of both maskable alarm and parent alarm | Only while parent alarm is active | An alarm can be suppressed by a parent alarm to minimize confusion during an alarm flood and build an alarm hierarchy |
| 4 | OnDelayed | Automatic upon activation of on-delalyable alarm | Short with expiration | An alarm with an on-delay is temporarily suppressed upon activation to minimize fleeting/chattering |  
| 5 | Shelved | Manual Operator Command | Short with expiration | An alarm can be temporarily suppressed via manual operator command |
| 6 | OffDelayed† | Automatic upon de-activation of off-delayable alarm | Short with expiration | An alarm with an off-delay is temporarily incited upon de-activation to minimize fleeting/chattering |
| 7 | Latched† | Automatic upon activation of latachable alarm | Until Operator Ack | A fleeting alarm (one that toggles between active and not active too quickly) can be configured to require acknowledgement by operators - the alarm is latched once active and won't clear to Normal (or Active) until acknowledged |

_† Incited alarm override (Others are suppressed override)_

**Note**: Some overrides are disallowed by configuration.  The registered-alarms topic schema contains fields indicating whether an alarm is filterable, maskable (maskedby), on-delayable (ondelayseconds), off-delayable (offdelayseconds), and latchable (latching).

## Alarm States
The effective alarm state is computed by the [alarm-state-processor](https://github.com/JeffersonLab/alarm-state-processor), which consumes the registered-alarms, active-alarms, and overridden-alarms topics and outputs to the alarm-state topic the effective alarm state.  The effective alarm state takes into consideration override precedence, one shot vs continuous shelving, and active vs inactive combinations with overridden considerations.  The alarm states in precedence order:

| Precedence | State                     | Active | Effectively | Note                                                    |
|------------|---------------------------|--------|------------ |---------------------------------------------------------|
| 1          | NormalDisabled            | No     | Normal      | Until disable removed (suppressed)                      |
| 2          | Disabled                  | Yes    | Normal      | Until disable removed OR the alarm becomes inactive (suppressed)       |
| 3          | NormalFiltered            | No     | Normal      | Until the filter is removed (suppressed)                               |
| 4          | Filtered                  | Yes    | Normal      | Until the filter is removed OR the alarm becomes inactive (suppressed) |
| 5          | Masked                    | Yes    | Normal      | Until the alarm or parent alarm becomes inactive (suppressed)          |
| 6          | OnDelayed                 | Yes    | Normal      | Until delay expires OR the alarm becomes inactive (suppressed)         |
| 7          | OneShotShelved            | Yes    | Normal      | Until the alarm becomes inactive OR shelving expires (suppressed)      |
| 8          | NormalContinuousShelved   | No     | Normal      | Until shelving expires (suppressed)                                    |
| 9          | ContinuousShelved         | Yes    | Normal      | Until delay expires OR the alarm becomes inactive (suppressed)         |
| 10         | OffDelayed                | No     | Active      | Until delay expires (incited)                        |
| 11         | NormalLatched             | No     | Active      | Until operator acknowledgement (incited)             |
| 12         | Latched                   | Yes    | Active      | Until operator acknowledgement OR the alarm becomes inactive (incited)    |
| 13         | Active                    | Yes    | Active      | Timely operator action is required                   |
| 14         | Normal                    | No     | Normal      | Does not require operator action                     |    

**Note**: Some states are mutually exclusive such as the override states with "Normal" prefix cannot occur at the same times as their Active counterparts (For example, an alarm can not be both NormalDisabled and Disabled at the same time, but an alarm can be both Disabled and Filtered).  The Precedence is arbitrary in these mutually exclusive cases.  The way our override schema is keyed it is also impossible for an alarm to be both One shot and continuous shelved simultaneously (they're also mutually exclusive states).

**Note**: Registration isn't really used to determine state at this time; just ensures an initial set of "Normal" alarms are recorded.

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
