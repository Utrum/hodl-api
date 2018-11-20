#!/usr/bin/env python
import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

consuming_q = 'process_queues_signal'
for q in ['unconfirmed', 'sendmany', consuming_q]:
    channel.queue_declare(queue=q, durable=True)


def get_unconfirmed_txs():
    q = 'unconfirmed'
    for n in range(0,10):
        method, header, body = channel.basic_get(queue=q)
        if body != None:
            output = json.loads(body.decode())
            print(output)
            channel.basic_ack(delivery_tag=method.delivery_tag)


def callback(ch, method, properties, body):
    output = json.loads(body.decode())
    print(output)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    get_unconfirmed_txs()


channel.basic_consume(callback, queue=consuming_q)
channel.start_consuming()

