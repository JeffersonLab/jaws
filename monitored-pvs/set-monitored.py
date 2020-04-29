import os

from confluent_kafka import avro, Producer
from confluent_kafka.avro import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer as AvroSerde

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
       "type" : "string"
     }
   ]
}
"""

value_schema = avro.loads(value_schema_str)
value = {"topic": "iocin1-heartbeat", "mask": ""}
key = "iocin1:heartbeat"


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
schema_registry = CachedSchemaRegistryClient(os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081'))

avro_serde = AvroSerde(schema_registry)
serialize_avro = avro_serde.encode_record_with_schema

p = Producer({
    'bootstrap.servers': bootstrap_servers,
    'on_delivery': delivery_report})

topic = 'monitored-pvs'
val_payload = serialize_avro(topic, value_schema, value, is_key=False)

p.produce(topic=topic, value=val_payload, key=key)
p.flush()
