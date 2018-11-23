import pika
import json


def send_process_queues_signal():
    q = 'process_queues_signal'
    msg = '{"process": true}'
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(
        queue=q,
        durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=q,
        body=msg,
        properties=pika.BasicProperties(delivery_mode=2))


def add_payee(msg, q):
    json_msg = json.dumps(msg)
    msg = json_msg
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(
        queue=q,
        durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=q,
        body=msg,
        properties=pika.BasicProperties(delivery_mode=2))

