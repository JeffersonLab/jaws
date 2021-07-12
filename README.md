<p>
<a href="#"><img align="right" width="200" height="150" src="https://raw.githubusercontent.com/JeffersonLab/kafka-alarm-system/master/logo.png"/></a>     
</p>


# JLab Alarm Warning System (JAWS) [![Docker](https://img.shields.io/docker/v/slominskir/jaws?sort=semver&label=DockerHub)](https://hub.docker.com/r/slominskir/jaws)
> "Don't get bit!"

An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project defines topic schemas, ties together the message pipeline services that make up the core alarm system in a docker-compose file, and provides Python scripts for configuring and interacting with the system.  JAWS attempts to comply with [ANSI/ISA 18.2-2016](https://www.isa.org/products/ansi-isa-18-2-2016-management-of-alarm-systems-for) where appropriate.

---
- [Overview](https://github.com/JeffersonLab/jaws#overview)
- [Quick Start with Compose](https://github.com/JeffersonLab/jaws#quick-start-with-compose)
- [Overrides](https://github.com/JeffersonLab/jaws#overrides)
   - [Incited Alarms](https://github.com/JeffersonLab/jaws#incited-alarms)
   - [Suppressed Alarms](https://github.com/JeffersonLab/jaws#suppressed-alarms)
- [Alarm States](https://github.com/JeffersonLab/jaws#alarm-states) 
- [Scripts](https://github.com/JeffersonLab/jaws#scripts)
- [Docker](https://github.com/JeffersonLab/jaws#docker)
- [See Also](https://github.com/JeffersonLab/jaws#see-also)
---

## Overview
The JAWS alarm system is composed primarily of three subsystems: _registered-alarms_, _active-alarms_, and _overridden-alarms_.   The inventory of all possible alarms is maintained by registering or unregistering alarm definitions on the _registered-alarms_ topic (the master alarm database).   Alarms are triggered active by producing messages on the _active-alarms_ topic.     An alarm can be overridden to either suppress or incite the active state by placing a message on the _overridden-alarms_ topic.  

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

## Overrides
An alarm can be in two basic states: 
  - "Active": Timely operator action required (actively alarming / annunciating)
  - "Normal": No operator action required

In an ideal world alarm producers are sophisticated and aware of the machine program and nuisance alarms are non-existent.  Nuisance alarms are alarms which are in the Active state incorrectly - there really isn't any operator action required despite the alarm producer indicating there is.   In practice, nuisance alarms are very common and quickly undermine the value of an alarm system.   Overrides are one way for operators to deal with nuisance alarms by adding a layer of indirection from alarm producers and allowing effective alarm state to differ from actual alarm state.

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
| 4 | OnDelayed | Automatic upon activation of on-delayable alarm | Short with expiration | An alarm with an on-delay is temporarily suppressed upon activation to minimize fleeting/chattering |  
| 5 | Shelved | Manual Operator Command | Short with expiration | An alarm can be temporarily suppressed via manual operator command |
| 6 | OffDelayed† | Automatic upon de-activation of off-delayable alarm | Short with expiration | An alarm with an off-delay is temporarily incited upon de-activation to minimize fleeting/chattering |
| 7 | Latched† | Automatic upon activation of latchable alarm | Until Operator Ack | A fleeting alarm (one that toggles between active and not active too quickly) can be configured to require acknowledgement by operators - the alarm is latched once active and won't clear to Normal (or Active) until acknowledged |

_† Incited alarm override (Others are suppressed override)_

**Note**: Some overrides are disallowed by configuration.  The registered-alarms topic schema contains fields indicating whether an alarm is filterable, maskable (maskedby), on-delayable (ondelayseconds), off-delayable (offdelayseconds), and latchable (latching).

## Alarm States
The effective alarm state is computed by the [alarm-state-processor](https://github.com/JeffersonLab/alarm-state-processor), which consumes the registered-alarms, active-alarms, and overridden-alarms topics and outputs to the alarm-state topic the effective alarm state.  The effective alarm state takes into consideration override precedence, one shot vs continuous shelving, and active vs inactive combinations with overridden considerations.  The alarm states in precedence order:

| Precedence | State                     | Actually | Effectively | Note                                                     |
|------------|---------------------------|--------|------------ |------------------------------------------------------------|
| 1          | NormalDisabled            | Normal | Normal      | Until disable removed (suppressed)                         |
| 2          | Disabled                  | Active | Normal      | Until disable removed OR the alarm becomes inactive (suppressed)       |
| 3          | NormalFiltered            | Normal | Normal      | Until the filter is removed (suppressed)                               |
| 4          | Filtered                  | Active | Normal      | Until the filter is removed OR the alarm becomes inactive (suppressed) |
| 5          | Masked                    | Active | Normal      | Until the alarm or parent alarm becomes inactive (suppressed)          |
| 6          | OnDelayed                 | Active | Normal      | Until delay expires OR the alarm becomes inactive (suppressed)         |
| 7          | OneShotShelved            | Active | Normal      | Until the alarm becomes inactive OR shelving expires (suppressed)      |
| 8          | NormalContinuousShelved   | Normal | Normal      | Until shelving expires (suppressed)                                    |
| 9          | ContinuousShelved         | Active | Normal      | Until delay expires OR the alarm becomes inactive (suppressed)         |
| 10         | OffDelayed                | Normal | Active      | Until delay expires (incited)                        |
| 11         | NormalLatched             | Normal | Active      | Until operator acknowledgement (incited)             |
| 12         | Latched                   | Active | Active      | Until operator acknowledgement OR the alarm becomes inactive (incited)    |
| 13         | Active                    | Active | Active      | Timely operator action is required                   |
| 14         | Normal                    | Normal | Normal      | Does not require operator action                     |    

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

**Note**: When developing the app you can mount the build artifact into the container by substituting the docker-compose up command with:
```
docker-compose -f docker-compose.yml -f docker-compose-dev.yml up
```

## See Also
 - [Software Design](https://github.com/JeffersonLab/jaws/wiki/Software-Design)
 - [Developer Notes](https://github.com/JeffersonLab/jaws/wiki/Developer-Notes)
