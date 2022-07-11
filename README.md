<p>
<a href="#"><img align="right" width="200" height="150" src="https://raw.githubusercontent.com/JeffersonLab/jaws/main/logo.png"/></a>     
</p>


# JLab Alarm Warning System (JAWS) [![CI](https://github.com/JeffersonLab/jaws/actions/workflows/ci.yml/badge.svg)](https://github.com/JeffersonLab/jaws/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/jaws-scripts)](https://pypi.org/project/jaws-scripts/) [![Docker](https://img.shields.io/docker/v/slominskir/jaws?label=DockerHub&sort=semver)](https://hub.docker.com/r/slominskir/jaws)
> "Don't get bit!"

An alarm system built on [Kafka](https://kafka.apache.org/) that supports pluggable alarm sources.  This project defines Kafka topics and [AVRO](https://avro.apache.org/) schemas, ties together the message pipeline services that make up the core alarm system in a docker-compose file, and provides Python scripts for configuring and interacting with the system.  JAWS attempts to comply with [ANSI/ISA 18.2-2016](https://www.isa.org/products/ansi-isa-18-2-2016-management-of-alarm-systems-for) where appropriate.

---
- [Overview](https://github.com/JeffersonLab/jaws#overview)
- [Quick Start with Compose](https://github.com/JeffersonLab/jaws#quick-start-with-compose)
- [Install](https://github.com/JeffersonLab/jaws#install) 
- [API](https://github.com/JeffersonLab/jaws#api)
- [Configure](https://github.com/JeffersonLab/jaws#configure)
- [Build](https://github.com/JeffersonLab/jaws#build) 
- [Test](https://github.com/JeffersonLab/jaws#test) 
- [Release](https://github.com/JeffersonLab/jaws#release) 
- [See Also](https://github.com/JeffersonLab/jaws#see-also)
---

## Overview
The JAWS alarm system is composed primarily of two subsystems: registrations and notifications.  

The inventory of all possible alarms (the master alarm database) are stored in Kafka as alarm instances, and these instances are organized into classes so that some properties are provided by their assigned alarm class.  The alarm instances are maintained on the _alarm-instances_ topic.  Alarm classes define group-shared properties such as corrective action and rationale and are persisted on the _alarm-classes_ topic.   The JAWS effective processor joins classes to instances to form effective alarm registrations on the _effective-registrations_ topic.   

Activations indicate an alarm is annunciating (active), and timely operator action is required.  Alarms are triggered active by producing messages on the _alarm-activations_ topic.  An alarm can be overridden to either suppress or incite the active state by placing a message on the _alarm-overrides_ topic.  The effective notification state considering both activations and overrides is calculated by JAWS from _activations_ and _overrides_ and made available on the _effective-notifications_ topic. 

Both effective registrations and effective notifications are combined by the JAWS effective processor on the _effective-alarms_ topic.

**Services**
- [jaws-effective-processor](https://github.com/JeffersonLab/jaws-effective-processor): Process classes and overrides and provide effective state on the _effective-registrations_, _effective-notifications_, and _effective-alarms_ topics
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

## Quick Start with Compose 
1. Grab project
```
git clone https://github.com/JeffersonLab/jaws
cd jaws
```
2. Launch Docker
```
docker compose up
```
3. Monitor active alarms
```
docker exec -it jaws /scripts/client/list_activations.py --monitor
```
4. Trip an alarm  
```
docker exec jaws /scripts/client/set_activation.py alarm1
```
**Note**: The docker-compose services require significant system resources - tested with 4 CPUs and 4GB memory.

**See**: [Docker Compose Strategy](https://gist.github.com/slominskir/a7da801e8259f5974c978f9c3091d52c)

**See**: More [Usage Examples](https://github.com/JeffersonLab/jaws/wiki/Usage-Examples)

## Install
### Core scripts
Requires [Python 3.9+](https://www.python.org/)

```
pip install jaws-scripts
```

**Note**: It's generally recommended to use a Python virtual environment to avoid dependency conflicts (else a dedicated Docker container can be used).

### Entire application
The entire JAWS application consists of multiple microservices and each one has a separate installation.  However, you can launch them all using the docker compose [here](https://github.com/JeffersonLab/jaws/blob/main/examples/compose/all.yml).   This compose file (and it's references) answers the question of which version of each microservice to use.   In a production environment you'll likely want to use some orchestration tooling, which could be literally anything from bash scripts leveraging `systemctl --host` to Ansible/Chef/Puppet/Whatever, or perhaps Kubernetes + tooling.

## API
Admin Scripts API

[Sphinx Docs](https://jeffersonlab.github.io/jaws/)


## Configure
The following environment variables are required by the scripts:

| Name             | Description                                                                                                                |
|------------------|----------------------------------------------------------------------------------------------------------------------------|
| BOOTSTRAP_SERVER | Host and port pair pointing to a Kafka server to bootstrap the client connection to a Kafka Cluster; example: `kafka:9092` |
| SCHEMA_REGISTRY  | URL to Confluent Schema Registry; example: `http://registry:8081`                                                          |

The Docker container requires the script environment variables, plus can optionally handle the following environment variables as well:

| Name            | Description                                                                                                                                                                                                                                                                                                                                             |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ALARM_LOCATIONS | Path to an alarm locations file to import ([example file](https://github.com/JeffersonLab/jaws/blob/main/examples/data/locations)), else an https URL to a file, else a comma separated list of location definitions with fields separated by the pipe symbol.  Example Inline CSV: `name\|parent` |
| ALARM_CATEGORIES | Path to an alarm categories file to import ([example file](https://github.com/JeffersonLab/jaws/blob/main/examples/data/categories)), else an https URL to a file, else a comma separated list of catgory definitions with fields.  Example Inline CSV: `name` |
| ALARM_CLASSES   | Path to an alarm classes file to import ([example file](https://github.com/JeffersonLab/jaws/blob/main/examples/data/classes)), else an https URL to a file, else a comma separated list of class definitions with fields separated by the pipe symbol.  Example Inline CSV: `name\|category\|priority\|rationale\|correctiveaction\|pointofcontactusername\|latching\|filterable\|ondelayseconds\|offdelayseconds` |
| ALARM_INSTANCES | Path to an alarm instances file to import ([example file](https://github.com/JeffersonLab/jaws/blob/main/examples/data/instances)), else an https URL to a file, else a comma separated list of instance definitions with fields separated by the pipe symbol.  Leave epicspv field empty for SimpleProducer. Example Inline CSV: `name\|class\|epicspv\|location\|maskedby\|screencommand` |

## Build
This [Python 3.9+](https://www.python.org/) project is built with [setuptools](https://setuptools.pypa.io/en/latest/setuptools.html) and may be run using either the Python [virtual environment](https://docs.python.org/3/tutorial/venv.html) feature or a dedicated Docker container to isolate dependencies.   The [pip](https://pypi.org/project/pip/) tool can be used to download dependencies.  Docker was used extensively for development due to the dependency on the Kafka ecosystem.

```
git clone https://github.com/JeffersonLab/jaws
cd jaws
python -m build
```

**Note for JLab On-Site Users**: Jefferson Lab has an intercepting [proxy](https://gist.github.com/slominskir/92c25a033db93a90184a5994e71d0b78)

**See**: [Python Development Notes](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1) and [Docker Development Quick Reference](https://gist.github.com/slominskir/a7da801e8259f5974c978f9c3091d52c#development-quick-reference)

## Test
The integration tests require a docker container environment and are run automatically as a GitHub Action on git push.   You can also run tests from a local workstation using the following instructions:

1. Start Docker Test environment
```
docker compose -f test.yml up
```
2. Execute Tests
```
docker exec -i jaws bash -c "cd /tests; pytest -p no:cacheprovider"
```
**Note**: You can also run tests directly on the host (instead of inside the jaws container) if you set the environment variables as: 
`BOOTSTRAP_SERVERS=localhost:9094` and `SCHEMA_REGISTRY=http://localhost:8081`

## Release
1. Bump the version number in setup.cfg and commit and push to GitHub (using [Semantic Versioning](https://semver.org/)).   
2. Create a new release on the GitHub [Releases](https://github.com/JeffersonLab/jaws/releases) page corresponding to same version in setup.cfg (Enumerate changes and link issues)
3. Clean build by removing `build`, `dist`, and `docsrc/source/_autosummary` directories
4. Activate [virtual env](https://gist.github.com/slominskir/e7ed71317ea24fc19b97a0ec006ff4f1#activate-dev-virtual-environment)
5. From venv build package, build docs, lint, test, and publish new artifact to PyPi with:
```
python -m build
sphinx-build -b html docsrc/source build/docs
pylint src/jaws_scripts
python -m twine upload --repository pypi dist/*
```
6. Build and push [Docker image](https://gist.github.com/slominskir/a7da801e8259f5974c978f9c3091d52c#8-build-an-image-based-of-github-tag)
7. Update Sphinx docs by copying them from build dir into gh-pages branch and updating index.html (commit, push).

## See Also
 - [Overrides and Effective State](https://github.com/JeffersonLab/jaws/wiki/Overrides-and-Effective-State)
 - [Software Design](https://github.com/JeffersonLab/jaws/wiki/Software-Design)
 - [Developer Notes](https://github.com/JeffersonLab/jaws/wiki/Developer-Notes)
