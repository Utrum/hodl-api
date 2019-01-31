#!/usr/bin/env python3
# written by patrick hennis

import bitcoin
import bitcoin.rpc
from conf.coin import CoinParams
from conf.mongodb import AddressParam
from pymongo import MongoClient
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("--height", help="set block height to start scan at")
args = parser.parse_args()

bitcoin.params = bitcoin.core.coreparams = CoinParams()
proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)

connection = MongoClient(AddressParam.ADDRESS, AddressParam.PORT)
db = connection.mydb
collection = db.txs

if args.height:
    height = args.height
else:
    height = 1

block = proxy.call('getblock', str(height))


def eliminateDecimal(tx):
    for v in tx['vout']:
        v['value'] = float(v['value'])
    return tx


def process(dtx):
    addrs = []
    dtx = eliminateDecimal(dtx)
    for v in dtx['vout']:
        if 'addresses' in v['scriptPubKey']:
            if v['scriptPubKey']['addresses'][0][0] == 'b':
                amount = dtx['vout'][0]['value']
            ta = v['scriptPubKey']['addresses']
            for a in ta:
                addrs.append(a)

    data = {'txid': tx, 'height': block['height'], 'addresses': addrs, 'amount': float(amount), 'tx': dtx}
    collection.insert(data)


while True:
    if 'nextblockhash' in block:
        for tx in block['tx']:
            rawtx = proxy.call('getrawtransaction', tx)
            dtx = proxy.call('decoderawtransaction', rawtx)
            vout = dtx['vout']
            if len(vout) > 1:
                asm = vout[1]['scriptPubKey']['asm']
                if 'OP_RETURN' in asm:
                    try:
                        asmd = bytes.fromhex(asm[10:]).decode('ascii')
                        if 'REDEEM SCRIPT' in asmd:
                            process(dtx)
                    except Exception as e:
                        pass
                        # print(e)
        height = int(height) + 1
        block = proxy.call('getblock', str(height))
    else:
        print("sleeping")
        time.sleep(60)
