#!/usr/bin/env python3
# written by patrick hennis

import requests
from conf.mongodb import AddressParam
from pymongo import MongoClient
import argparse
import time


# connection to mongodb
connection = MongoClient(AddressParam.ADDRESS, AddressParam.PORT)
db = connection.db
collection = db.txs


# parser for command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--height", help="set block height to start scan at")
args = parser.parse_args()


# if a height was passed through arguments, set the var to that height
if args.height:
    height = int(args.height)
else:
    # if not set the starting height to one heigher than what was last scanned
    for x in db.txs.find({},{"last_block_scanned":1,"_id":0}):
        if x:
            height = x['last_block_scanned']+1


# updates record in db that keeps track of last scanned block
def updateLastBlock(height):
    for x in db.txs.find({},{"last_block_scanned":1,"_id":0}):
        if x:
            scanned_height = x['last_block_scanned']
    db.txs.update({'last_block_scanned':scanned_height},{'last_block_scanned':(height)})


# gets block data at height
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


# method for processing transactions
def process(tx):
    addrs = []
    # iterates through the vout field
    for v in tx['vout']:
        # get value from tx
        if 'addresses' in v['scriptPubKey']:
            if v['scriptPubKey']['addresses'][0][0] == 'b':
                amount = tx['vout'][0]['value']
            # get all addresses involved in tx
            ta = v['scriptPubKey']['addresses']
            for a in ta:
                addrs.append(a)

    # create data to be inserted
    data = {'txid': tx['txid'], 'height': tx['blockheight'], 'addresses': addrs, 'amount': float(amount), 'tx': tx}
    collection.insert(data)
    # for testing
    print('inserted: ' + str(data))

# get first block at specified height
block = getBlockAtHeight(height)

while True:
    # for testing
    print(height)
    # make sure there is next block
    if block['txs'][0]['confirmations'] > 0:
        # iterate through all txs in block
        for tx in block['txs']:
            vout = tx['vout']
            if len(vout) > 1:
                asm = vout[1]['scriptPubKey']['asm']
                # check to make sure it is HODL tx
                if 'OP_RETURN' in asm:
                    try:
                        # decode hex
                        asmd = bytes.fromhex(asm[10:]).decode('ascii')
                        if 'REDEEM SCRIPT' in asmd:
                            process(tx)
                    except Exception as e:
                        # print for testing
                        print(e)
                        pass
        # increase height
        height = int(height) + 1
        # get next block
        block = getBlockAtHeight(height)
        # update last block scanned record
        updateLastBlock(height)
    else:
        # at most recent block
        print("sleeping")
        time.sleep(60)
