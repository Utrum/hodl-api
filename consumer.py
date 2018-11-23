#!/usr/bin/env python
import pika
import json
import requests
from conf.coin import CoinParams
from mq import add_payee


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

consuming_q = 'process_queues_signal'
for q in ['unconfirmed', 'confirmed', 'transactions', consuming_q]:
    channel.queue_declare(queue=q, durable=True)

batch_length = 3


def is_confirmed(addr, txid):
    url = CoinParams.EXPLORER
    url += '/insight-api-komodo/addr/' + addr + '/utxo'
    try:
        r = requests.get(
            url,
            headers={'Content-type': 'text/plain; charset=utf-8'})
        utxos = json.loads(r.text)
    except Exception as e:
        print("Couldn't connect to " + url, e)
    try:
        for utxo in utxos:
            if utxo['txid'] == txid:
                if utxo['confirmations'] >= 2:
                    return(True)
                else:
                    return(False)
        raise Exception(
            "Transaction id " + txid + " not found, for address " + addr)
    except Exception as e:
        print(
            "Exception found while validating confirmations on address " +
            addr, e)


def filter_txs():
    q = 'transactions'
    output = False
    for n in range(0, batch_length):
        method, header, body = channel.basic_get(queue=q)
        if body is not None:
            output = True
            msg_json = json.loads(body.decode())
            txid = msg_json['hodlFundTxId']
            addr = msg_json['payeeAddress']
            try:
                confirmed = is_confirmed(addr, txid)
                if confirmed is True:
                    print("Added transaction " + txid + ' to "confirmed" queue.')
                    add_payee(msg_json, 'confirmed')
                else:
                    print(txid + " still unconfirmed.")
                    add_payee(msg_json, 'unconfirmed')
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                raise Exception(e)
    return(output)


def pay_confirmed_txs():
    q = 'confirmed'
    output = False
    for n in range(0, batch_length):
        method, header, body = channel.basic_get(queue=q)
        if body is not None:
            output = True
            msg_json = json.loads(body.decode())
            print("should pay:")
            print(msg_json)
            channel.basic_ack(delivery_tag=method.delivery_tag)
    return(output)


def requeue_txs():
    q = 'unconfirmed'
    output = False
    method, header, body = channel.basic_get(queue=q)
    if body is not None:
        output = True
        msg_json = json.loads(body.decode())
        txid = msg_json['hodlFundTxId']
        print("Re-queuing", txid)
        add_payee(msg_json, 'transactions')
        channel.basic_ack(delivery_tag=method.delivery_tag)
    return(output)


def callback(ch, method, properties, body):
    ch.basic_ack(delivery_tag=method.delivery_tag)
    while requeue_txs() is True:
        pass
    while filter_txs() is True:
        print("Transactions processed.")
    while pay_confirmed_txs() is True:
        print("Reward payment done.")


channel.basic_consume(callback, queue=consuming_q)
channel.start_consuming()

