from confluent_kafka.avro import AvroConsumer
from confluent_kafka.avro.serializer import SerializerError
from confluent_kafka import OFFSET_BEGINNING

c = AvroConsumer({
    'bootstrap.servers': 'localhost',
    'group.id': 'list-monitored.sh',
    'schema.registry.url': 'http://127.0.0.1:8081'})

def my_on_assign(consumer, partitions):
    # We are assuming one partition, otherwise low/high would each be array and checking against high water mark would probably not work since other partitions could still contain unread messages.
    global low
    global high
    for p in partitions:
        p.offset = OFFSET_BEGINNING
        low, high = c.get_watermark_offsets(p)
    consumer.assign(partitions)

c.subscribe(['monitored-pvs'], on_assign=my_on_assign)

while True:
    try:
        msg = c.poll(1.0)

    except SerializerError as e:
        print("Message deserialization failed for {}: {}".format(msg, e))
        break

    if msg is None:
        continue

    if msg.error():
        print("AvroConsumer error: {}".format(msg.error()))
        continue

    print(msg.key(), msg.value())

    if msg.offset() + 1 == high:
        break


c.close()
