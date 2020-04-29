# kafka-alarm-scripts
Bash and Python scripts for managing alarms in Kafka

The alarm system consists of a few subsystems:

| Subsystem | Description | Topics | Key Schema | Value Schema | Scripts |
|----------|---------------|----------|-----------|-----------|----------|
| monitored-pvs | Set of monitored pvs | monitored-pvs |  String: EPICS CA PV name | AVRO: monitored-pvs-value | set-monitored.py, unset-monitored.py, list-monitored.py |
| alarms | Set of all possible alarm metadata (descriptions).  Some alarms may come from sources other than directly from an EPICS CA PV alarm such as from evaluating custom conditions/rules. | alarms | String: name | AVRO: alarms-value | set-alarm.py, unset-alarm.py, list-alarms.py |
| shelved-alarms | Set of alarms that have been shelved. | shelved-alarms | String: name | AVRO: shelved-alarms-value | set-shelved.py, unset-shelved.py, list-shelved.py |
| active-alarms | Set of alarms currently active (alarming). | active-alarms | String: name | AVRO: active-alarms-value | set-active.py, unset-active.py, list-active.py |

The alarm system relies on Kafka not only for notification of changes, but for Event Sourcing - everything is stored in Kafka and the entire state of
the system is built by replaying messages.   All topics have compaction enabled to remove old messages that would be overwritten on replay.  Compaction is not very aggressive though so some candidates for deletion are often lingering when clients connect so they must be prepared to handle the ordered messages on replay as if ones later may overwrite ones earlier.
