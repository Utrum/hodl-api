#!/usr/bin/env python
import pika
import json
import requests
import time
import bitcoin.rpc
from bitcoin.core import b2lx
from conf.coin import CoinParams
from conf.mq import mqhost
from mq import to_queue


BATCH_LENGTH = 3
REQ_CONFS = 2


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=mqhost))
channel = connection.channel()

consuming_q = 'process_queues_signal'
for q in ['unconfirmed', 'confirmed', 'transactions', consuming_q]:
    channel.queue_declare(queue=q, durable=True)


def sendmany(payments):
    proxy = bitcoin.rpc.Proxy(btc_conf_file=CoinParams.CONF_FILE)
    output = proxy.sendmany("", payments)
    return(output)


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
                if utxo['confirmations'] >= REQ_CONFS:
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
    method, header, body = channel.basic_get(queue=q)
    if body is not None:
        output = True
        msg_json = json.loads(body.decode())
        txid = msg_json['hodlFundTxId']
        addr = msg_json['payeeAddress']
        try:
            confirmed = is_confirmed(addr, txid)
            if confirmed is True:
                print(
                    "Moving transaction " + txid + ' to "confirmed" queue.')
                to_queue(msg_json, 'confirmed')
            else:
                print(txid + " still unconfirmed.")
                to_queue(msg_json, 'unconfirmed')
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            raise Exception(e)
    return(output)


def pay_confirmed_txs():
    q = 'confirmed'
    output = False
    payments = {}
    delivery_tags = []
    for n in range(0, BATCH_LENGTH):
        method, header, body = channel.basic_get(queue=q)
        if body is not None:
            output = True
            msg_json = json.loads(body.decode())
            address = msg_json['payeeAddress']
            amount = msg_json['reward']
            payments[address] = amount
            delivery_tags.append(method.delivery_tag)
    try:
        if len(delivery_tags) > 0:
            print("\nPaying:")
            print(payments)
            sendmany_output = b2lx(sendmany(payments))
            print("Transaction ID:", sendmany_output)
            for dtag in delivery_tags:
                channel.basic_ack(delivery_tag=dtag)
    except Exception as e:
        print(e)
    return(output)


def requeue_txs():
    q = 'unconfirmed'
    output = False
    method, header, body = channel.basic_get(queue=q)
    if body is not None:
        output = True
        msg_json = json.loads(body.decode())
        txid = msg_json['hodlFundTxId']
        print("Re-queuing " + txid + " for check out.")
        to_queue(msg_json, 'transactions')
        channel.basic_ack(delivery_tag=method.delivery_tag)
    return(output)


def callback(ch, method, properties, body):
    ch.basic_ack(delivery_tag=method.delivery_tag)
    timestamp = str(int(time.time()))
    print(timestamp + ' ==================')
    while requeue_txs() is True:
        pass
    while filter_txs() is True:
        pass
    while pay_confirmed_txs() is True:
        print("Reward payment operation finished.")
    print("=============================\n")


channel.basic_consume(callback, queue=consuming_q)
channel.start_consuming()

