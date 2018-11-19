#!/usr/bin/env python3
import pika
import json

def add_payee(msg):
    json_msg = json.dumps(msg)
    msg = json_msg
    print(msg)
    q = 'unconfirmed'
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(
        queue = q,
        durable = True)
    channel.basic_publish(
        exchange = '',
        routing_key = q,
        body = msg,
        properties = pika.BasicProperties(
            delivery_mode = 2)
    )

