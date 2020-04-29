# kafka-alarm-scripts
Bash and Python scripts for managing alarms in Kafka

The alarm system consists of a few subsystems:

| Subsystem | Description | Topics | Schemas | Scripts |
|----------|---------------|----------|-----------|-----------|
| monitored-pvs | Set of monitored pvs, keyed by EPICS CA PV name. | monitored-pvs | monitored-pvs-value | set-monitored.py, unset-monitored.py, list-monitored.py |
| alarms | Set of all possible alarm metadata (descriptions), keyed by name.  Some alarms may come from sources other than directly from an EPICS CA PV alarm such as from evaluating custom conditions/rules. | alarms | alarms-value | set-alarm.py, unset-alarm.py, list-alarms.py |
| shelved-alarms | Set of alarms that have been shelved. | shelved-alarms | shelved-alarms-value | set-shelved.py, unset-shelved.py, list-shelved.py |
| active-alarms | Set of alarms currently active (alarming). | active-alarms | active-alarms-value | set-active.py, unset-active.py, list-active.py |

The alarm system relies on Kafka not only for notification of changes, but for Event Sourcing - everything is stored in Kafka and the entire state of
the system is built by replaying messages.   All topics have compaction enabled to remove old messages that would be overwritten on replay.
