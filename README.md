# kafka-alarm-system
An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.

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
docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic active-alarms
```
4. Trip an EPICS alarm
```
docker exec softioc caput hello 1
```

The alarm system is composed of the following services:
   - Kafka - distributed message system
   - ZooKeeper - required by Kafka for bookkeeping and coordination
   - Schema Registry - message schema lookup
   
Alarms are triggered by producing messages on the active-alarms topic, which is generally done programmatically via Kafka Connect and Kafka Streams services.  For example EPICS alarms are handled by:  
   - [Connect EPICS](https://github.com/JeffersonLab/epics2kafka) - transfer EPICS CA messages into Kafka, one topic per EPICS channel
   - Streams EPICS Alarms - conditionally consolidates and propogates EPICS alarms read from Connect EPICS topics to the __active-alarms__ topic based on configuration in the master __alarms__ topic

Anything can produce messages on the active-alarms topic (with proper authorization).

## Scripts
Bash and Python scripts for managing alarms in [Kafka](https://kafka.apache.org/).  Schemas are stored in the [Schema Registry](https://github.com/confluentinc/schema-registry) in [AVRO](https://avro.apache.org/) format.

The alarm system consists of a few subsystems:

| Subsystem | Description | Topics | Key Schema | Value Schema | Scripts |
|----------|---------------|----------|-----------|-----------|----------|
| alarms | Set of all possible alarm metadata (descriptions).  Some alarms may come from sources other than directly from an EPICS CA PV alarm such as from evaluating custom conditions/rules. | alarms | String: alarm name | AVRO: alarms-value | set-alarm.py, list-alarms.py |
| shelved-alarms | Set of alarms that have been shelved. | shelved-alarms | String: alarm name | AVRO: shelved-alarms-value | set-shelved.py, list-shelved.py |
| active-alarms | Set of alarms currently active (alarming). | active-alarms | String: alarm name | AVRO: active-alarms-value | set-active.py, list-active.py |

The alarm system relies on Kafka not only for notification of changes, but for [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) - everything is stored in Kafka and the entire state of
the system is built by replaying messages.   All topics have compaction enabled to remove old messages that would be overwritten on replay.  Compaction is not very aggressive though so some candidates for deletion are often lingering when clients connect so they must be prepared to handle the ordered messages on replay as ones later in the stream may overwrite ones earlier.

To unset (remove) a record use the --unset option with the "set" scripts, This writes a null/None tombstone record.  To modify a record simply set a new one with the same key as the message stream is ordered and newer records overwrite older ones.  To see all options use the --help option.  Instead of documenting the AVRO schemas here, just dump them using the dump-schemas.sh script.  They are self-documenting.

## Python Environment
Scripts tested with Python 3.7.6

Generally recommended to use a Python virtual environment to avoid dependency conflicts.  You can use the requirements.txt file to ensure the Python module dependences are installed:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

*Note*: [Jefferson Lab Internal Proxy](https://github.com/JeffersonLab/kafka-alarm-scripts/wiki/JeffersonLabProxy)

## Configure
By default the scripts assume you are executing them on the same box as a standalone Kafka with zookeeper and Schema Registry with Kafka installed at /opt/kafka/pro.  To modify the defaults set the following environment variables:

| Variable | Default |
|----------|---------|
| ZOOKEEPER | `localhost:2181` |
| BOOTSTRAP_SERVERS | `localhost:9092` |
| SCHEMA_REGISTRY | `http://localhost:8081` |
| KAFKA_HOME | `/opt/kafka/pro` |

## See
   - [Kafka EPICS CA Connector](https://github.com/JeffersonLab/epics2kafka)
