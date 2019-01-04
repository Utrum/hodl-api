#!/usr/bin/env python3

import bitcoin
import bitcoin.rpc
from conf.coin import CoinParams
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--height", help="set block height to start scan at")
args = parser.parse_args()

bitcoin.params = bitcoin.core.coreparams = CoinParams()
proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)


if args.height:
    block = proxy.call('getblock', str(args.height))
else:
    block = proxy.call('getblock', str(0))

print(block['tx'])
# print(block['height'])

for tx in block['tx']:
    rawtx = proxy.call('getrawtransaction', tx)
    print(proxy.call('decoderawtransaction', rawtx))
