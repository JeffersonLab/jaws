# kafka-alarm-system
An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project ties together all of the services that make up the alarm system in a docker-compose file and adds an alarm system console Docker image containing Python scripts for configuring and interacting with the system.

## Quick Start with Docker 
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
docker exec -it console /scripts/active-alarms/list-active.py --monitor
```
4. Trip an alarm  
```
docker exec console /scripts/active-alarms/set-active.py channel1 --priority P1_LIFE
```
[Scripts Reference](https://github.com/JeffersonLab/kafka-alarm-system/wiki/Scripts-Reference)

The alarm system is composed of the following services:
   - Kafka - distributed message system
   - [ZooKeeper](https://zookeeper.apache.org/) - required by Kafka for bookkeeping and coordination
   - [Schema Registry](https://github.com/confluentinc/schema-registry) - message schema lookup
   - Alarm Console - defined in this project; provides Python scripts for setup and interacting with the alarm system
   
Alarms are triggered by producing messages on the __active-alarms__ topic, which is generally done programmatically via Kafka Connect or Kafka Streams services.  For example EPICS alarms could be handled by the additional service: [epics2Kafka](https://github.com/JeffersonLab/epics2kafka).  Anything can produce messages on the active-alarms topic (with proper authorization).

**Note**: The docker-compose services require significant system resources - tested with 4 CPUs and 4GB memory.

## Alarm System Console

### Scripts
Python scripts for managing alarms in [Kafka](https://kafka.apache.org/).  Schemas are stored in the [Schema Registry](https://github.com/confluentinc/schema-registry) in [AVRO](https://avro.apache.org/) format.

The alarm system consists of a few subsystems:

| Subsystem | Description | Topics | Key Schema | Value Schema | Scripts |
|----------|---------------|----------|-----------|-----------|----------|
| alarms | Set of all possible alarm metadata (descriptions).  Alarms may come from a variety of sources such as from an EPICS alarm service.  A custom alarm service (Kafka Streams) could evaluate custom conditions/rules.  All alarms that are possible should be registered here. | alarms | String: alarm name | AVRO: alarms-value | set-alarm.py, list-alarms.py |
| shelved-alarms | Set of alarms that have been shelved. | shelved-alarms | String: alarm name | AVRO: shelved-alarms-value | set-shelved.py, list-shelved.py |
| active-alarms | Set of alarms currently active (alarming). | active-alarms | String: alarm name | AVRO: active-alarms-value | set-active.py, list-active.py |

The alarm system relies on Kafka not only for notification of changes, but for [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) - everything is stored in Kafka and the entire state of
the system is built by replaying messages.   All topics have compaction enabled to remove old messages that would be overwritten on replay.  Compaction is not very aggressive though so some candidates for deletion are often lingering when clients connect so they must be prepared to handle the ordered messages on replay as ones later in the stream may overwrite ones earlier.

To unset (remove) a record use the --unset option with the "set" scripts, This writes a null/None tombstone record.  To modify a record simply set a new one with the same key as the message stream is ordered and newer records overwrite older ones.  To see all options use the --help option.  Instead of documenting the AVRO schemas here, just dump them using the dump-schemas.sh script.  They are self-documenting. 

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

*Note*: [Jefferson Lab Internal Proxy](https://github.com/JeffersonLab/kafka-alarm-scripts/wiki/JeffersonLabProxy)

### Configure
By default the scripts assume you are executing them on the same box as a standalone Kafka with and Schema Registry.  To modify the defaults set the following environment variables:

| Variable | Default |
|----------|---------|
| BOOTSTRAP_SERVERS | `localhost:9092` |
| SCHEMA_REGISTRY | `http://localhost:8081` |
