import json
import logging
import os
import pkgutil
import pwd
import signal
from abc import ABC, abstractmethod
from typing import Dict, Any

import fastavro
import time
from confluent_kafka import SerializingProducer
from confluent_kafka.cimpl import Message
from confluent_kafka.schema_registry import SchemaRegistryClient, SchemaReference, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.serialization import StringDeserializer, StringSerializer
from jlab_jaws.avro.entities import AlarmClass, AlarmPriority, UnionEncoding, NoteAlarming, EPICSAlarming, \
    SimpleAlarming, EPICSSEVR, EPICSSTAT, AlarmActivationUnion, OverriddenAlarmType, AlarmOverrideKey, \
    AlarmOverrideUnion, DisabledOverride, FilteredOverride, LatchedOverride, ShelvedReason, ShelvedOverride, \
    OffDelayedOverride, OnDelayedOverride, MaskedOverride, AlarmLocation, SimpleProducer, EPICSProducer, CALCProducer, \
    AlarmInstance
from jlab_jaws.avro.serde import _unwrap_enum
from jlab_jaws.eventsource.cached_table import CachedTable, log_exception
from jlab_jaws.eventsource.listener import EventSourceListener
from jlab_jaws.serde.avro import AvroDeserializerWithReferences, AvroSerializerWithReferences
from tabulate import tabulate

logger = logging.getLogger(__name__)


class MonitorListener(EventSourceListener):

    def on_highwater_timeout(self) -> None:
        pass

    def on_batch(self, msgs: Dict[Any, Message]) -> None:
        for msg in msgs.values():
            print("{}={}".format(msg.key(), msg.value()))

    def on_highwater(self) -> None:
        pass


class Serde(ABC):
    @abstractmethod
    def from_json(self, data):
        pass

    @abstractmethod
    def to_json(self, data):
        pass

    @abstractmethod
    def serializer(self):
        pass

    @abstractmethod
    def deserializer(self):
        pass


class StringSerde(Serde):
    def from_json(self, data):
        return data

    def to_json(self, data):
        return data

    def serializer(self):
        return StringSerializer('utf_8')

    def deserializer(self):
        return StringDeserializer('utf_8')


class RegistryAvroSerde(Serde):
    def __init__(self, schema_registry_client, schema):
        self._schema_registry_client = schema_registry_client
        self._schema = schema

    @abstractmethod
    def from_dict(self, data):
        pass

    def _from_dict_with_ctx(self, data, ctx):
        return self.from_dict(data)

    @abstractmethod
    def to_dict(self, data):
        pass

    def _to_dict_with_ctx(self, data, ctx):
        return self.to_dict(data)

    def from_json(self, data):
        pass

    def to_json(self, data):
        sorteddata = dict(sorted(self.to_dict(data).items()))
        jsondata = json.dumps(sorteddata)
        return jsondata

    def get_schema(self) -> Schema:
        return self._schema

    def get_schema_str(self) -> str:
        return self._schema_str

    def serializer(self):
        """
            Return a serializer.

            :return: Serializer
        """

        return AvroSerializer(self._schema_registry_client,
                              self._schema.schema_str,
                              self._to_dict_with_ctx,
                              None)

    def deserializer(self):
        """
            Return an AlarmActivationUnion deserializer.

            :return: Deserializer
        """

        return AvroDeserializer(self._schema_registry_client,
                                None,
                                self._from_dict_with_ctx,
                                True)


class RegistryAvroWithReferencesSerde(RegistryAvroSerde):
    def __init__(self, schema_registry_client, schema, references, named_schemas):
        self._references = references
        self._named_schemas = named_schemas

        super().__init__(schema_registry_client, schema)

    @abstractmethod
    def from_dict(self, data):
        pass

    @abstractmethod
    def to_dict(self, data):
        pass

    def references(self):
        return self._references

    def named_schemas(self):
        return self._named_schemas

    def serializer(self):
        """
                Return a serializer.

                :return: Serializer
            """
        return AvroSerializerWithReferences(self._schema_registry_client,
                                            self.get_schema(),
                                            self._to_dict_with_ctx,
                                            None,
                                            self.named_schemas())

    def deserializer(self):
        """
                Return a deserializer.

                :return: Deserializer
            """
        return AvroDeserializerWithReferences(self._schema_registry_client,
                                              None,
                                              self._from_dict_with_ctx,
                                              True,
                                              self.named_schemas())


class ClassSerde(RegistryAvroWithReferencesSerde):
    """
        Provides AlarmClass serde utilities
    """

    def __init__(self, schema_registry_client):

        priority_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmPriority.avsc")
        priority_schema_str = priority_bytes.decode('utf-8')

        named_schemas = {}

        ref_dict = json.loads(priority_schema_str)
        fastavro.parse_schema(ref_dict, named_schemas=named_schemas)

        priority_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmPriority", "alarm-priority", 1)
        references = [priority_schema_ref]

        schema_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmClass.avsc")
        schema_str = schema_bytes.decode('utf-8')

        schema = Schema(schema_str, "AVRO", references)

        super().__init__(schema_registry_client, schema, references, named_schemas)

    def to_dict(self, data):
        """
            Converts an AlarmClass to a dict.

            :param data: The AlarmClass
            :return: A dict
        """

        if data is None:
            return None

        return {
            "category": data.category,
            "priority": data.priority.name,
            "rationale": data.rationale,
            "correctiveaction": data.corrective_action,
            "pointofcontactusername": data.point_of_contact_username,
            "latching": data.latching,
            "filterable": data.filterable,
            "ondelayseconds": data.on_delay_seconds,
            "offdelayseconds": data.off_delay_seconds
        }

    def from_dict(self, data):
        """
            Converts a dict to an AlarmClass.

            :param data: The dict
            :return: The AlarmClass
            """
        if data is None:
            return None

        return AlarmClass(data.get('category'),
                          _unwrap_enum(data.get('priority'), AlarmPriority),
                          data.get('rationale'),
                          data.get('correctiveaction'),
                          data.get('pointofcontactusername'),
                          data.get('latching'),
                          data.get('filterable'),
                          data.get('ondelayseconds'),
                          data.get('offdelayseconds'))


class LocationSerde(RegistryAvroSerde):
    """
        Provides AlarmLocation serde utilities
    """

    def __init__(self, schema_registry_client):

        schema_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmLocation.avsc")
        schema_str = schema_bytes.decode('utf-8')

        schema = Schema(schema_str, "AVRO", [])

        super().__init__(schema_registry_client, schema)

    def to_dict(self, data):
        """
        Converts AlarmLocation to a dict.

        :param data: The AlarmLocation
        :return: A dict
        """
        return {
            "parent": data.parent
        }

    def from_dict(self, data):
        """
        Converts a dict to AlarmLocation.

        :param data: The dict
        :return: The AlarmLocation
        """
        return AlarmLocation(data['parent'])


class ActivationSerde(RegistryAvroSerde):
    """
        Provides AlarmActivationUnion serde utilities
    """

    def __init__(self, schema_registry_client, union_encoding=UnionEncoding.TUPLE):

        self._union_encoding = union_encoding

        schema_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmActivationUnion.avsc")
        schema_str = schema_bytes.decode('utf-8')

        schema = Schema(schema_str, "AVRO", [])

        super().__init__(schema_registry_client, schema)

    def to_dict(self, data):
        """
        Converts an AlarmActivationUnion to a dict.

        :param data: The AlarmActivationUnion
        :return: A dict
        """

        if data is None:
            return None

        if isinstance(data.msg, SimpleAlarming):
            uniontype = "org.jlab.jaws.entity.SimpleAlarming"
            uniondict = {}
        elif isinstance(data.msg, EPICSAlarming):
            uniontype = "org.jlab.jaws.entity.EPICSAlarming"
            uniondict = {"sevr": data.msg.sevr.name, "stat": data.msg.stat.name}
        elif isinstance(data.msg, NoteAlarming):
            uniontype = "org.jlab.jaws.entity.NoteAlarming"
            uniondict = {"note": data.msg.note}
        else:
            raise Exception("Unknown alarming union type: {}".format(data.msg))

        if self._union_encoding is UnionEncoding.TUPLE:
            union = (uniontype, uniondict)
        elif self._union_encoding is UnionEncoding.DICT_WITH_TYPE:
            union = {uniontype: uniondict}
        else:
            union = uniondict

        return {
            "msg": union
        }

    def from_dict(self, data):
        """
        Converts a dict to an AlarmActivationUnion.

        Note: UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported.

        :param data: The dict
        :return: The AlarmActivationUnion
        """

        if data is None:
            return None

        unionobj = data['msg']

        if type(unionobj) is tuple:
            uniontype = unionobj[0]
            uniondict = unionobj[1]
        elif type(unionobj is dict):
            value = next(iter(unionobj.items()))
            uniontype = value[0]
            uniondict = value[1]
        else:
            raise Exception("Unsupported union encoding")

        if uniontype == "org.jlab.jaws.entity.NoteAlarming":
            obj = NoteAlarming(uniondict['note'])
        elif uniontype == "org.jlab.jaws.entity.EPICSAlarming":
            obj = EPICSAlarming(_unwrap_enum(uniondict['sevr'], EPICSSEVR), _unwrap_enum(uniondict['stat'],
                                                                                         EPICSSTAT))
        else:
            obj = SimpleAlarming()

        return AlarmActivationUnion(obj)


class InstanceSerde(RegistryAvroSerde):
    """
        Provides AlarmInstance serde utilities
    """

    def __init__(self, schema_registry_client, union_encoding=UnionEncoding.TUPLE):

        self._union_encoding = union_encoding

        schema_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmInstance.avsc")
        schema_str = schema_bytes.decode('utf-8')

        schema = Schema(schema_str, "AVRO", [])

        super().__init__(schema_registry_client, schema)

    def to_dict(self, data):
        """
        Converts an AlarmInstance to a dict.

        :param data: The AlarmInstance
        :return: A dict
        """

        if data is None:
            return None

        if isinstance(data.producer, SimpleProducer):
            uniontype = "org.jlab.jaws.entity.SimpleProducer"
            uniondict = {}
        elif isinstance(data.producer, EPICSProducer):
            uniontype = "org.jlab.jaws.entity.EPICSProducer"
            uniondict = {"pv": data.producer.pv}
        elif isinstance(data.producer, CALCProducer):
            uniontype = "org.jlab.jaws.entity.CALCProducer"
            uniondict = {"expression": data.producer.expression}
        else:
            raise Exception("Unknown instance producer union type: {}".format(data.producer))

        if self._union_encoding is UnionEncoding.TUPLE:
            union = (uniontype, uniondict)
        elif self._union_encoding is UnionEncoding.DICT_WITH_TYPE:
            union = {uniontype: uniondict}
        else:
            union = uniondict

        return {
            "class": data.alarm_class,
            "producer": union,
            "location": data.location,
            "maskedby": data.masked_by,
            "screencommand": data.screen_command
        }

    def from_dict(self, data):
        """
        Converts a dict to an AlarmInstance.

        Note: UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported.

        :param data: The dict
        :return: The AlarmInstance
        """

        if data is None:
            return None

        unionobj = data['producer']

        if type(unionobj) is tuple:
            uniontype = unionobj[0]
            uniondict = unionobj[1]
        elif type(unionobj is dict):
            value = next(iter(unionobj.items()))
            uniontype = value[0]
            uniondict = value[1]
        else:
            raise Exception("Unsupported union encoding")

        if uniontype == "org.jlab.jaws.entity.CalcProducer":
            producer = CALCProducer(uniondict['expression'])
        elif uniontype == "org.jlab.jaws.entity.EPICSProducer":
            producer = EPICSProducer(uniondict['pv'])
        else:
            producer = SimpleProducer()

        return AlarmInstance(data.get('class'),
                             producer,
                             data.get('location'),
                             data.get('maskedby'),
                             data.get('screencommand'))


class OverrideKeySerde(RegistryAvroSerde):
    def __init__(self, schema_registry_client):
        schema_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmOverrideKey.avsc")
        schema_str = schema_bytes.decode('utf-8')

        schema = Schema(schema_str, "AVRO", [])

        super().__init__(schema_registry_client, schema)

    def to_dict(self, data):
        """
        Converts an AlarmOverrideKey to a dict.

        :param data: The AlarmOverrideKey
        :return: A dict
        """
        return {
            "name": data.name,
            "type": data.type.name
        }

    def from_dict(self, data):
        """
        Converts a dict to an AlarmOverrideKey.

        :param data: The dict
        :return: The AlarmOverrideKey
        """
        return AlarmOverrideKey(data['name'], _unwrap_enum(data['type'], OverriddenAlarmType))


class OverrideSerde(RegistryAvroWithReferencesSerde):
    def __init__(self, schema_registry_client, union_encoding=UnionEncoding.TUPLE):

        self._union_encoding = union_encoding

        disabled_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/DisabledOverride.avsc")
        disabled_schema_str = disabled_bytes.decode('utf-8')

        filtered_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/FilteredOverride.avsc")
        filtered_schema_str = filtered_bytes.decode('utf-8')

        latched_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/LatchedOverride.avsc")
        latched_schema_str = latched_bytes.decode('utf-8')

        masked_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/MaskedOverride.avsc")
        masked_schema_str = masked_bytes.decode('utf-8')

        off_delayed_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/OffDelayedOverride.avsc")
        off_delayed_schema_str = off_delayed_bytes.decode('utf-8')

        on_delayed_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/OnDelayedOverride.avsc")
        on_delayed_schema_str = on_delayed_bytes.decode('utf-8')

        shelved_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/ShelvedOverride.avsc")
        shelved_schema_str = shelved_bytes.decode('utf-8')

        named_schemas = {}

        ref_dict = json.loads(disabled_schema_str)
        fastavro.parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = json.loads(filtered_schema_str)
        fastavro.parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = json.loads(latched_schema_str)
        fastavro.parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = json.loads(masked_schema_str)
        fastavro.parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = json.loads(off_delayed_schema_str)
        fastavro.parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = json.loads(on_delayed_schema_str)
        fastavro.parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = json.loads(shelved_schema_str)
        fastavro.parse_schema(ref_dict, named_schemas=named_schemas)

        disabled_schema_ref = SchemaReference("org.jlab.jaws.entity.DisabledOverride", "disabled-override", 1)
        filtered_schema_ref = SchemaReference("org.jlab.jaws.entity.FilteredOverride", "filtered-override", 1)
        latched_schema_ref = SchemaReference("org.jlab.jaws.entity.LatchedOverride", "latched-override", 1)
        masked_schema_ref = SchemaReference("org.jlab.jaws.entity.MaskedOverride", "masked-override", 1)
        off_delayed_schema_ref = SchemaReference("org.jlab.jaws.entity.OffDelayedOverride", "off-delayed-override", 1)
        on_delayed_schema_ref = SchemaReference("org.jlab.jaws.entity.OnDelayedOverride", "on-delayed-override", 1)
        shelved_schema_ref = SchemaReference("org.jlab.jaws.entity.ShelvedOverride", "shelved-override", 1)

        references = [disabled_schema_ref,
                      filtered_schema_ref,
                      latched_schema_ref,
                      masked_schema_ref,
                      off_delayed_schema_ref,
                      on_delayed_schema_ref,
                      shelved_schema_ref]

        schema_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmOverrideUnion.avsc")
        schema_str = schema_bytes.decode('utf-8')

        schema = Schema(schema_str, "AVRO", references)

        super().__init__(schema_registry_client, schema, references, named_schemas)

    def to_dict(self, data):
        """
        Converts an AlarmOverrideUnion to a dict.

        :param data: The AlarmOverrideUnion
        :return: A dict
        """
        if isinstance(data.msg, DisabledOverride):
            uniontype = "org.jlab.jaws.entity.DisabledOverride"
            uniondict = {"comments": data.msg.comments}
        elif isinstance(data.msg, FilteredOverride):
            uniontype = "org.jlab.jaws.entity.FilteredOverride"
            uniondict = {"filtername": data.msg.filtername}
        elif isinstance(data.msg, LatchedOverride):
            uniontype = "org.jlab.jaws.entity.LatchedOverride"
            uniondict = {}
        elif isinstance(data.msg, MaskedOverride):
            uniontype = "org.jlab.jaws.entity.MaskedOverride"
            uniondict = {}
        elif isinstance(data.msg, OnDelayedOverride):
            uniontype = "org.jlab.jaws.entity.OnDelayedOverride"
            uniondict = {"expiration": data.msg.expiration}
        elif isinstance(data.msg, OffDelayedOverride):
            uniontype = "org.jlab.jaws.entity.OffDelayedOverride"
            uniondict = {"expiration": data.msg.expiration}
        elif isinstance(data.msg, ShelvedOverride):
            uniontype = "org.jlab.jaws.entity.ShelvedOverride"
            uniondict = {"expiration": data.msg.expiration, "comments": data.msg.comments,
                         "reason": data.msg.reason.name, "oneshot": data.msg.oneshot}
        else:
            print("Unknown alarming union type: {}".format(data.msg))
            uniontype = None
            uniondict = None

        if self._union_encoding is UnionEncoding.TUPLE:
            union = (uniontype, uniondict)
        elif self._union_encoding is UnionEncoding.DICT_WITH_TYPE:
            union = {uniontype: uniondict}
        else:
            union = uniondict

        return {
            "msg": union
        }

    def from_dict(self, data):
        """
        Converts a dict to an AlarmOverrideUnion.

        Note: Both UnionEncoding.TUPLE and UnionEncoding.DICT_WITH_TYPE are supported,
        but UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported at this time
        because I'm lazy and not going to try to guess what type is in your union.

        :param data: The dict (or maybe it's a duck)
        :return: The AlarmOverrideUnion
        """
        alarmingobj = data['msg']

        if type(alarmingobj) is tuple:
            alarmingtype = alarmingobj[0]
            alarmingdict = alarmingobj[1]
        elif type(alarmingobj is dict):
            value = next(iter(alarmingobj.items()))
            alarmingtype = value[0]
            alarmingdict = value[1]
        else:
            raise Exception("Unsupported union encoding")

        if alarmingtype == "org.jlab.jaws.entity.DisabledOverride":
            obj = DisabledOverride(alarmingdict['comments'])
        elif alarmingtype == "org.jlab.jaws.entity.FilteredOverride":
            obj = FilteredOverride(alarmingdict['filtername'])
        elif alarmingtype == "org.jlab.jaws.entity.LatchedOverride":
            obj = LatchedOverride()
        elif alarmingtype == "org.jlab.jaws.entity.MaskedOverride":
            obj = MaskedOverride()
        elif alarmingtype == "org.jlab.jaws.entity.OnDelayedOverride":
            obj = OnDelayedOverride(alarmingdict['expiration'])
        elif alarmingtype == "org.jlab.jaws.entity.OffDelayedOverride":
            obj = OffDelayedOverride(alarmingdict['expiration'])
        elif alarmingtype == "org.jlab.jaws.entity.ShelvedOverride":
            obj = ShelvedOverride(alarmingdict['expiration'], alarmingdict['comments'],
                                  _unwrap_enum(alarmingdict['reason'], ShelvedReason), alarmingdict['oneshot'])
        else:
            print("Unknown alarming type: {}".format(data['msg']))
            obj = None

        return AlarmOverrideUnion(obj)


class JAWSConsumer(CachedTable):

    def __init__(self, topic, consumer_name, key_serde, value_serde):
        self._topic = topic
        self._consumer_name = consumer_name
        self._key_serde = key_serde
        self._value_serde = value_serde

        set_log_level_from_env()

        signal.signal(signal.SIGINT, self.__signal_handler)

        ts = time.time()

        bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
        config = {'topic': topic,
                  'bootstrap.servers': bootstrap_servers,
                  'key.deserializer': key_serde.deserializer(),
                  'value.deserializer': value_serde.deserializer(),
                  'group.id': consumer_name + str(ts)}

        super().__init__(config)

    def print_records_continuous(self):
        self.add_listener(MonitorListener())
        self.start(log_exception)

    def print_table(self, msg_to_list, head=[], nometa=False, filter_if=lambda key, value: True):
        records = self.get_records()

        table = []

        if not nometa:
            head = ["Timestamp", "User", "Host", "Produced By"] + head

        for record in records.values():
            row = self.__get_row(record, msg_to_list, filter_if, nometa)
            if row is not None:
                table.append(row)

        # Truncate long cells
        table = [[(c if len(str(c)) < 30 else str(c)[:27] + "...") for c in row] for row in table]

        print(tabulate(table, head))

    def export_records(self, filter_if=lambda key, value: True):
        records = self.get_records()

        sortedtuples = sorted(records.items())

        for item in sortedtuples:
            key = item[1].key()
            value = item[1].value()

            if filter_if(key, value):
                key_json = self._key_serde.to_json(key)
                value_json = self._value_serde.to_json(value)

                print(key_json + '=' + value_json)

    def get_records(self) -> Dict[Any, Message]:
        self.start(log_exception)
        records = self.await_get(5)
        self.stop()
        return records

    def __get_row(self, msg: Message, msg_to_list, filter_if, nometa):
        timestamp = msg.timestamp()
        headers = msg.headers()

        row = msg_to_list(msg)

        if not nometa:
            row_header = self.__get_row_header(headers, timestamp)
            row = row_header + row

        if filter_if(msg.key(), msg.value()):
            if not nometa:
                row = row_header + row
        else:
            row = None

        return row

    def __get_row_header(self, headers, timestamp):
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

        return [ts, user, host, producer]

    def __signal_handler(self, sig, frame):
        print('Stopping from Ctrl+C!')
        self.stop()


class JAWSProducer:
    """
        This class produces messages with the JAWS expected header.

        Sensible defaults are used to determine BOOTSTRAP_SERVERS (look in env)
        and to handle errors (log them).

        This producer also knows how to import records from a file using the JAWS expected file format.
    """

    def __init__(self, topic, producer_name, key_serializer, value_serializer):
        set_log_level_from_env()

        self._topic = topic
        self._producer_name = producer_name

        bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
        producer_conf = {'bootstrap.servers': bootstrap_servers,
                         'key.serializer': key_serializer,
                         'value.serializer': value_serializer}

        self._producer = SerializingProducer(producer_conf)
        self._headers = self.__get_headers()

    def send(self, key, value):
        logger.debug("{}={}".format(key, value))
        self._producer.produce(topic=self._topic, headers=self._headers, key=key, value=value,
                               on_delivery=self.__on_delivery)
        self._producer.flush()

    def import_records(self, file, line_to_kv):
        logger.debug("Loading file", file)
        handle = open(file, 'r')
        lines = handle.readlines()

        for line in lines:
            key, value = line_to_kv(line)

            logger.debug("{}={}".format(key, value))
            self._producer.produce(topic=self._topic, headers=self._headers, key=key, value=value,
                                   on_delivery=self.__on_delivery)

        self._producer.flush()

    def __get_headers(self):
        return [('user', pwd.getpwuid(os.getuid()).pw_name),
                ('producer', self._producer_name),
                ('host', os.uname().nodename)]

    @staticmethod
    def __on_delivery(err, msg):
        if err is not None:
            logger.error('Failed: {}'.format(err))
        else:
            logger.debug('Delivered')


def set_log_level_from_env():
    level = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(threadName)-16s %(name)s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S')


def get_registry_client():
    sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    return SchemaRegistryClient(sr_conf)
