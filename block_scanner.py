#!/usr/bin/env python3
# written by patrick hennis

import requests
from conf.mongodb import AddressParam
from pymongo import MongoClient
import argparse
import time

connection = MongoClient(AddressParam.ADDRESS, AddressParam.PORT)
db = connection.db
collection = db.txs

parser = argparse.ArgumentParser()
parser.add_argument("--height", help="set block height to start scan at")
args = parser.parse_args()

if args.height:
    height = int(args.height)
else:
    for x in db.txs.find({},{"last_block_scanned":1,"_id":0}):
        if x:
            height = x['last_block_scanned']

def updateLastBlock(height):
    for x in db.txs.find({},{"last_block_scanned":1,"_id":0}):
        if x:
            scanned_height = x['last_block_scanned']
    db.txs.update({'last_block_scanned':scanned_height},{'last_block_scanned':(height)})

def getBlockAtHeight(height):
    # must start at 1
    if height < 1:
        raise ValueError('Height must be greater than zero')
    # get blockhash of specified height
    r = requests.get('http://95.179.150.75:3001/insight-api-komodo/block-index/' + str(height))
    print(r)
    blockhash = r.json()['blockHash']
    # get block data
    b = requests.get('http://95.179.150.75:3001/insight-api-komodo/txs/?block=' + blockhash)
    return(b.json())


def process(tx):
    addrs = []
    for v in tx['vout']:
        if 'addresses' in v['scriptPubKey']:
            if v['scriptPubKey']['addresses'][0][0] == 'b':
                amount = tx['vout'][0]['value']
            ta = v['scriptPubKey']['addresses']
            for a in ta:
                addrs.append(a)

    data = {'txid': tx['txid'], 'height': tx['blockheight'], 'addresses': addrs, 'amount': float(amount), 'tx': tx}
    collection.insert(data)
    print('inserted: ' + str(data))

block = getBlockAtHeight(height)

while True:
    print(height)
    if block['txs'][0]['confirmations'] > 0:
        for tx in block['txs']:
            vout = tx['vout']
            if len(vout) > 1:
                asm = vout[1]['scriptPubKey']['asm']
                if 'OP_RETURN' in asm:
                    try:
                        asmd = bytes.fromhex(asm[10:]).decode('ascii')
                        if 'REDEEM SCRIPT' in asmd:
                            process(tx)
                    except Exception as e:
                        print(e)
                        pass
        height = int(height) + 1
        block = getBlockAtHeight(height)
        updateLastBlock(height)
    else:
        print("sleeping")
        time.sleep(60)
