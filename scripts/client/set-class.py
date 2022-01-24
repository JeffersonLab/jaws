#!/usr/bin/env python3

import click
import json

from jlab_jaws.avro.clients import CategoryConsumer, ClassProducer
from jlab_jaws.avro.serde import ClassSerde
from jlab_jaws.avro.entities import AlarmClass
from jlab_jaws.avro.entities import AlarmPriority


def line_to_kv(line):
    tokens = line.split("=", 1)
    key = tokens[0]
    value_obj = tokens[1]
    value_dict = json.loads(value_obj)
    value = ClassSerde.from_dict(value_dict)

    return key, value


consumer = CategoryConsumer('set-class.py')
categories = consumer.records()


@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON "
                   "encoded AVRO formatted per the alarm-classes-value schema")
@click.option('--unset', is_flag=True, help="Remove the class")
@click.option('--category', type=click.Choice(categories), help="The alarm category")
@click.option('--priority', type=click.Choice(AlarmPriority._member_names_), help="The alarm priority")
@click.option('--filterable/--not-filterable', is_flag=True, default=True,
              help="True if alarm can be filtered out of view")
@click.option('--latching/--not-latching', is_flag=True, default=True,
              help="Indicate that the alarm latches and requires acknowledgement to clear")
@click.option('--pointofcontactusername', help="The point of contact user name")
@click.option('--rationale', help="The alarm rationale")
@click.option('--correctiveaction', help="The corrective action")
@click.option('--ondelayseconds', type=int, default=None, help="Number of on delay seconds")
@click.option('--offdelayseconds', type=int, default=None, help="Number of off delay seconds")
@click.argument('name')
def cli(file, unset, category,
        priority, filterable, latching, pointofcontactusername, rationale,
        correctiveaction, ondelayseconds, offdelayseconds, name):
    producer = ClassProducer('set-class.py')

    key = name

    if file:
        producer.import_records(name, line_to_kv)
    else:
        if unset:
            value = None
        else:
            if category is None:
                raise click.ClickException("--category required")

            if priority is None:
                raise click.ClickException("--priority required")

            if rationale is None:
                raise click.ClickException("--rationale required")

            if correctiveaction is None:
                raise click.ClickException("--correctiveaction required")

            if pointofcontactusername is None:
                raise click.ClickException("--pointofcontactusername required")

            value = AlarmClass(category,
                               AlarmPriority[priority],
                               rationale,
                               correctiveaction,
                               pointofcontactusername,
                               latching,
                               filterable,
                               ondelayseconds,
                               offdelayseconds)

        producer.send(key, value)


cli()
