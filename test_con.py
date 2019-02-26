#!/usr/bin/env python3
# test script written by patrick hennis

from pymongo import MongoClient
from conf.mongodb import AddressParam
import json

connection = MongoClient(AddressParam.ADDRESS, 27017)
db = connection.db
collection = db.txs


txs = []
def get_tx_data(address):
    for record in collection.find({'addresses': address}):
        txs.append(record['tx']['time'])
    return(txs)

if __name__ == '__main__':
    data = get_tx_data('RVzUGW75o9s2k83yFavV47SVC6DdiwCuzq')
    for d in data:
        print(d)


# data = {'txid': '0248162ade99647e96c44890cd3316f8d0860eb9db71a52b2531c887c5a55766'}
#
# x = collection.insert_one(data)
#
# for x in collection.find():
#   print(x)



# to find record
# print(db.txs.find({},{"last_block_scanned":1,"_id":0}))
#
# for x in db.txs.find({},{"last_block_scanned":1,"_id":0}):
#     height = x['last_block_scanned']
# db.txs.update({'last_block_scanned':height},{'last_block_scanned':(height+1)})
# for x in db.txs.find({},{"last_block_scanned":1,"_id":0}):
#     height = x['last_block_scanned']
#     print(height)
