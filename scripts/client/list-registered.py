#!/usr/bin/env python3

import os
import types
import click
import time
import json

from json import loads

from io import BytesIO
from struct import unpack
from fastavro import schemaless_reader

from tabulate import tabulate

from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient, _MAGIC_BYTE, topic_subject_name_strategy
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer, SerializationError
from confluent_kafka import OFFSET_BEGINNING


from confluent_kafka.schema_registry import Schema

from fastavro import parse_schema


def _schema_loads(schema_str):
    """
    Instantiates a Schema instance from a declaration string
    Args:
        schema_str (str): Avro Schema declaration.
    .. _Schema declaration:
        https://avro.apache.org/docs/current/spec.html#schemas
    Returns:
        Schema: Schema instance
    """
    schema_str = schema_str.strip()

    # canonical form primitive declarations are not supported
    if schema_str[0] != "{":
        schema_str = '{"type":"' + schema_str + '"}'

    return Schema(schema_str, schema_type='AVRO')


class _ContextStringIO(BytesIO):
    """
    Wrapper to allow use of StringIO via 'with' constructs.
    """

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


class AvroDeserializerWithReferences(AvroDeserializer):
    __slots__ = ['_reader_schema', '_registry', '_from_dict', '_writer_schemas', '_return_record_name', '_named_schemas']

    def __init__(self, schema_registry_client, schema=None, from_dict=None, return_record_name=False, named_schemas={}):
        self._registry = schema_registry_client
        self._writer_schemas = {}

        self._reader_schema = schema
        self._named_schemas = named_schemas

        if from_dict is not None and not callable(from_dict):
            raise ValueError("from_dict must be callable with the signature"
                             " from_dict(SerializationContext, dict) -> object")
        self._from_dict = from_dict

        self._return_record_name = return_record_name
        if not isinstance(self._return_record_name, bool):
            raise ValueError("return_record_name must be a boolean value")

    def __call__(self, value, ctx):
        """
        Decodes a Confluent Schema Registry formatted Avro bytes to an object.
        Arguments:
            value (bytes): bytes
            ctx (SerializationContext): Metadata pertaining to the serialization
                operation.
        Raises:
            SerializerError: if an error occurs ready data.
        Returns:
            object: object if ``from_dict`` is set, otherwise dict. If no value is supplied None is returned.
        """  # noqa: E501
        if value is None:
            return None

        if len(value) <= 5:
            raise SerializationError("Message too small. This message was not"
                                     " produced with a Confluent"
                                     " Schema Registry serializer")

        with _ContextStringIO(value) as payload:
            magic, schema_id = unpack('>bI', payload.read(5))
            if magic != _MAGIC_BYTE:
                raise SerializationError("Unknown magic byte. This message was"
                                         " not produced with a Confluent"
                                         " Schema Registry serializer")

            writer_schema = self._writer_schemas.get(schema_id, None)

            if writer_schema is None:
                schema = self._registry.get_schema(schema_id)
                prepared_schema = _schema_loads(schema.schema_str)
                writer_schema = parse_schema(loads(
                    prepared_schema.schema_str), _named_schemas=self._named_schemas)
                self._writer_schemas[schema_id] = writer_schema

            obj_dict = schemaless_reader(payload,
                                         writer_schema,
                                         self._reader_schema,
                                         self._return_record_name)

            if self._from_dict is not None:
                return self._from_dict(obj_dict, ctx)

            return obj_dict











scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = scriptpath + '/../../'

with open(projectpath + '/config/shared-schemas/AlarmCategory.avsc', 'r') as file:
    category_schema_str = file.read()

with open(projectpath + '/config/subject-schemas/registered-alarms-value.avsc', 'r') as file:
    value_schema_str = file.read()

bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
schema_registry_client = SchemaRegistryClient(sr_conf)

category_schema = Schema(category_schema_str, "AVRO", [])
schema = Schema(value_schema_str, "AVRO", [category_schema])

named_schemas = {}
cat_dict = loads(category_schema_str)
parse_schema(cat_dict, _named_schemas=named_schemas)

avro_deserializer = AvroDeserializerWithReferences(schema_registry_client, None, None, False, named_schemas)
string_deserializer = StringDeserializer('utf_8')

ts = time.time()

consumer_conf = {'bootstrap.servers': bootstrap_servers,
                 'key.deserializer': string_deserializer,
                 'value.deserializer': avro_deserializer,
                 'group.id': 'list-registered.py' + str(ts)}


registered = {}

empty = False

def my_on_assign(consumer, partitions):
    # We are assuming one partition, otherwise low/high would each be array and checking against high water mark would probably not work since other partitions could still contain unread messages.
    global low
    global high
    global empty
    for p in partitions:
        p.offset = OFFSET_BEGINNING
        low, high = consumer.get_watermark_offsets(p)
        if high == 0:
            empty = True
    consumer.assign(partitions)

def disp_row(msg):
    row = get_row(msg)
    if(row is not None):
        print(row) # TODO: format with a row template!

def get_row(msg):
    timestamp = msg.timestamp()
    headers = msg.headers()
    key = msg.key()
    value = msg.value()

    row = [key, value["producer"], value["location"], value["category"], value["priority"], value["rationale"], value["correctiveaction"], value["pointofcontactusername"], value["latching"], value["filterable"], value["maskedby"], value["screenpath"]]

    ts = time.ctime(timestamp[1] / 1000)

    user = ''
    producer = ''
    host = ''

    if headers is not None:
        lookup = dict(headers)
        bytez = lookup.get('user', b'')
        user = bytez.decode()
        bytez = lookup.get('producer', b'')
        producer = bytez.decode()
        bytez = lookup.get('host', b'')
        host = bytez.decode()

    if params.category is None or (value is not None and params.category == value['category']):
        if not params.nometa:
            row = [ts, user, host, producer] + row
    else:
        row = None

    return row

def disp_table():

    head=["Alarm Name", "Producer", "Location", "Category", "Priority", "Rationale", "Corrective Action", "P.O.C. Username", "Latching", "Filterable", "Masked By", "Screen Path"]
    table = []

    if not params.nometa:
        head = ["Timestamp", "User", "Host", "Produced By"] + head

    for msg in registered.values():
        row = get_row(msg)
        if(row is not None):
            table.append(row)

    print(tabulate(table, head))


def export():
    for msg in registered.values():
        key = msg.key()
        value = msg.value()
   
        if params.category is None or (value is not None and params.category == value['category']):
            v = json.dumps(value)
            print(key + '=' + v)

def list():
    c = DeserializingConsumer(consumer_conf)

    c.subscribe(['registered-alarms'], on_assign=my_on_assign)

    while True:
        try:
            msg = c.poll(1.0)

        except SerializationError as e:
            print("Message deserialization failed for {}: {}".format(msg, e))
            break

        if empty:
            break

        if msg is None:
            continue

        if msg.error():
            print("AvroConsumer error: {}".format(msg.error()))
            continue

        if msg.value() is None:
            del registered[msg.key()]
        else:
            registered[msg.key()] = msg

        if msg.offset() + 1 == high:
            break

    if params.export:
        export()
    else:
        disp_table()

    if params.monitor:
        while True:
            try:
                msg = c.poll(1.0)

            except SerializationError as e:
                print("Message deserialization failed for {}: {}".format(msg, e))
                break

            if msg is None:
                continue

            if msg.error():
                print("AvroConsumer error: {}".format(msg.error()))
                continue

            disp_row(msg)

    c.close()


@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format such that they can be imported by set-registered.py; implies --nometa")
@click.option('--category', help="Only show registered alarms in the specified category")

def cli(monitor, nometa, export, category):
    global params

    params = types.SimpleNamespace()

    params.monitor = monitor
    params.nometa = nometa
    params.export = export
    params.category = category

    list()

cli()
