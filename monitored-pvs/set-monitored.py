import os
import types
import click

from confluent_kafka import avro, Producer
from confluent_kafka.avro import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer as AvroSerde
from avro.schema import Field

Field.to_json_old = Field.to_json

# Fixes an issue with python3-avro:
# https://github.com/confluentinc/confluent-kafka-python/issues/610
def to_json(self, names=None):
    to_dump = self.to_json_old(names)
    type_name = type(to_dump["type"]).__name__
    if type_name == "mappingproxy":
        to_dump["type"] = to_dump["type"].copy()
    return to_dump


Field.to_json = to_json

value_schema_str = """
{
   "namespace": "org.jlab",
   "name": "MonitoredPV",
   "type": "record",
   "fields" : [
     {
       "name" : "topic",
       "type" : "string"
     },
     {
       "name" : "mask",
       "type" : {
           "name" : "MonitorMask",
           "type" : "enum",
           "symbols" : ["VALUE","VALUE_ALARM","VALUE_ALARM_ATTRIBUTE"]
       }
     }
  ]
}
"""

test = """
                {
                  "name"      : "MonitorMask",
                  "namespace" : "org.jlab",
                  "type"      : "enum",
                  "symbols"   : ["VALUE","VALUE_ALARM","VALUE_ALARM_ATTRIBUTE"]
                }

"""

value_schema = avro.loads(value_schema_str)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered')

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
schema_registry = CachedSchemaRegistryClient(os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081'))

avro_serde = AvroSerde(schema_registry)
serialize_avro = avro_serde.encode_record_with_schema

p = Producer({
    'bootstrap.servers': bootstrap_servers,
    'on_delivery': delivery_report})

topic = 'monitored-pvs'

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = serialize_avro(topic, value_schema, params.value, is_key=False)

    p.produce(topic=topic, value=val_payload, key=params.key)
    p.flush()

@click.command()
@click.option('--unset', is_flag=True, help="Stop monitoring the specified PV")
@click.option('--topic', required=False, help="Topic to produce monitor messages on (because some pv names contain illegal topic characters)")
@click.option('--mask', required=False, type=click.Choice(['VALUE', 'VALUE_ALARM', 'VALUE_ALARM_ATTRIBUTE']), help="EPICS CA Monitor Mask")
@click.argument('name')

def cli(unset, topic, mask, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if unset:
        params.value = None
    else:
        if topic == None or mask == None:
            raise click.ClickException(
                    "Must specify options --topic and --mask")

        params.value = {"topic": topic, "mask": mask}

    send()

cli()

