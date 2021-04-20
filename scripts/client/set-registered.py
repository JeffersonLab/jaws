#!/usr/bin/env python3

import os
import pwd
import types
import click
import json

import avro.schema

from io import BytesIO
from json import loads
from fastavro import parse_schema, schemaless_writer
from struct import pack

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

from confluent_kafka.schema_registry import Schema, SchemaReference, _MAGIC_BYTE, topic_subject_name_strategy


class _ContextStringIO(BytesIO):
    """
    Wrapper to allow use of StringIO via 'with' constructs.
    """

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False



class AvroSerializerWithReferences(AvroSerializer):
    __slots__ = ['_hash', '_auto_register', '_known_subjects', '_parsed_schema',
                 '_registry', '_schema', '_schema_id', '_schema_name',
                 '_subject_name_func', '_to_dict', '_named_schemas']

    # default configuration
    _default_conf = {'auto.register.schemas': True,
                 'subject.name.strategy': topic_subject_name_strategy}

    def __init__(self, schema_registry_client, schema,
                 to_dict=None, conf=None, named_schemas={}):
        self._registry = schema_registry_client
        self._schema_id = None
        # Avoid calling registry if schema is known to be registered
        self._known_subjects = set()

        if to_dict is not None and not callable(to_dict):
            raise ValueError("to_dict must be callable with the signature"
                             " to_dict(object, SerializationContext)->dict")

        self._to_dict = to_dict
        self._named_schemas = named_schemas

        # handle configuration
        conf_copy = self._default_conf.copy()
        if conf is not None:
            conf_copy.update(conf)

        self._auto_register = conf_copy.pop('auto.register.schemas')
        if not isinstance(self._auto_register, bool):
            raise ValueError("auto.register.schemas must be a boolean value")

        self._subject_name_func = conf_copy.pop('subject.name.strategy')
        if not callable(self._subject_name_func):
            raise ValueError("subject.name.strategy must be callable")

        if len(conf_copy) > 0:
            raise ValueError("Unrecognized properties: {}"
                             .format(", ".join(conf_copy.keys())))

        schema_dict = loads(schema.schema_str)
        parsed_schema = parse_schema(schema_dict, _named_schemas=self._named_schemas)
        # The Avro spec states primitives have a name equal to their type
        # i.e. {"type": "string"} has a name of string.
        # This function does not comply.
        # https://github.com/fastavro/fastavro/issues/415
        schema_name = parsed_schema.get('name', schema_dict['type'])

        self._schema = schema
        self._schema_name = schema_name
        self._parsed_schema = parsed_schema

    def __call__(self, obj, ctx):
        """
        Serializes an object to the Confluent Schema Registry's Avro binary
        format.
        Args:
            obj (object): object instance to serializes.
            ctx (SerializationContext): Metadata pertaining to the serialization operation.
        Note:
            None objects are represented as Kafka Null.
        Raises:
            SerializerError: if any error occurs serializing obj
        Returns:
            bytes: Confluent Schema Registry formatted Avro bytes
        """
        if obj is None:
            return None

        subject = self._subject_name_func(ctx, self._schema_name)

        # Check to ensure this schema has been registered under subject_name.
        if self._auto_register and subject not in self._known_subjects:
            # The schema name will always be the same. We can't however register
            # a schema without a subject so we set the schema_id here to handle
            # the initial registration.
            self._schema_id = self._registry.register_schema(subject,
                                                             self._schema)
            self._known_subjects.add(subject)
        elif not self._auto_register and subject not in self._known_subjects:
            registered_schema = self._registry.lookup_schema(subject,
                                                             self._schema)
            self._schema_id = registered_schema.schema_id
            self._known_subjects.add(subject)

        if self._to_dict is not None:
            value = self._to_dict(obj, ctx)
        else:
            value = obj

        with _ContextStringIO() as fo:
            # Write the magic byte and schema ID in network byte order (big endian)
            fo.write(pack('>bI', _MAGIC_BYTE, self._schema_id))
            # write the record to the rest of the buffer
            schemaless_writer(fo, self._parsed_schema, value)

            return fo.getvalue()














scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

with open(projectpath + '/config/shared-schemas/AlarmCategory.avsc', 'r') as file:
    category_schema_str = file.read()

with open(projectpath + '/config/subject-schemas/registered-alarms-value.avsc', 'r') as file:
    value_schema_str = file.read()

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered')

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url':  os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

named_schemas = {}
ref_dict = loads(category_schema_str)
parse_schema(ref_dict, _named_schemas=named_schemas)

category_schema = Schema(category_schema_str, "AVRO", [])
category_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmCategory", "alarm-category", "1")
schema = Schema(value_schema_str, "AVRO", [category_schema_ref])

avro_serializer = AvroSerializerWithReferences(schema_registry_client, schema, None, None, named_schemas)

#value_schema = avro.schema.Parse(value_schema_str)

groups = []
locations = []
categories = ["RF"]
priorities = []

#groups = value_schema.fields[0].type.symbols
#locations = value_schema.fields[2].type.schemas[1].symbols
#categories = value_schema.fields[3].type.schemas[1].symbols
#priorities = value_schema.fields[4].type.schemas[1].symbols

producer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.serializer': StringSerializer('utf_8'),
                 'value.serializer': avro_serializer}
producer = SerializingProducer(producer_conf)

topic = 'registered-alarms'

hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),('producer','set-registered.py'),('host',os.uname().nodename)]

def send() :
    if params.value is None:
        val_payload = None
    else:
        val_payload = params.value

    producer.produce(topic=topic, value=val_payload, key=params.key, headers=hdrs, on_delivery=delivery_report)
    producer.flush()

def doImport(file) :
   print("Loading file", file)
   handle = open(file, 'r')
   lines = handle.readlines()

   for line in lines:
       tokens = line.split("=", 1)
       key = tokens[0]
       value = tokens[1]
       v = json.loads(value)
       print("{}={}".format(key, v))

       # Trying to work around union serialization issues: https://github.com/confluentinc/confluent-kafka-python/pull/785
       # Note that kafka-avro-console-consumer provided by Confluent requires proper JSON AVRO encoding https://avro.apache.org/docs/current/spec.html#json_encoding
       if 'org.jlab.alarms.EPICSProducer' in v['producer']:
           v['producer'] = v['producer']['org.jlab.alarms.EPICSProducer']
       elif 'org.jlab.alarms.StreamRuleProducer' in v['producer']:
           v['producer'] = v['producer']['org.jlab.alarms.StreamRuleProducer']
       else:
           v['producer'] = v['producer']['org.jlab.alarms.SimpleProducer']

       producer.produce(topic=topic, value=v, key=key, headers=hdrs)

   producer.flush()


@click.command()
@click.option('--file', is_flag=True, help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON encoded AVRO formatted per the registered-alarms-value schema")
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--group', type=click.Choice(groups), help="The alarm group")
@click.option('--producersimple', is_flag=True, help="Simple alarm (producer)")
@click.option('--producerpv', help="The name of the EPICS CA PV that directly powers this alarm")
@click.option('--producerexpression', help="The CALC expression used to generate this alarm")
@click.option('--location', type=click.Choice(locations), help="The alarm location")
@click.option('--category', type=click.Choice(categories), help="The alarm category")
@click.option('--priority', type=click.Choice(priorities), help="The alarm priority")
@click.option('--filterable', is_flag=True, default=None, help="True if alarm can be filtered out of view")
@click.option('--latching', is_flag=True, default=None, help="Indicate that the alarm latches and requires acknowledgement to clear")
@click.option('--screenpath', help="The path the alarm screen display")
@click.option('--pointofcontactusername', help="The point of contact user name")
@click.option('--rationale', help="The alarm rationale")
@click.option('--correctiveaction', help="The corrective action")
@click.option('--maskedby', help="The optional parent alarm that masks this one")
@click.argument('name')

def cli(file, unset, group, producersimple, producerpv, producerexpression, location, category, priority, filterable, latching, screenpath, pointofcontactusername, rationale, correctiveaction, maskedby, name):
    global params

    params = types.SimpleNamespace()

    params.key = name

    if(file):
        doImport(name)
    else:
        if unset:
            params.value = None
        else:
            if producersimple == False and producerpv == None and producerexpression == None:
                raise click.ClickException("Must specify one of --producersimple, --producerpv, --producerexpression")

            if producersimple:
                producer = {}
            elif producerpv:
                producer = {"pv": producerpv}
            else:
                producer = {"expression" : producerexpression}

            params.value = {"group": group, "producer": producer, "location": location, "category": category, "priority": priority, "filterable": filterable, "latching": latching, "screenpath": screenpath, "pointofcontactusername": pointofcontactusername, "rationale": rationale, "correctiveaction": correctiveaction, "maskedby": maskedby}

            if group is None:
                params.value["group"] = "Default_Group"

            print('Message: {}'.format(params.value))

        send()

cli()

