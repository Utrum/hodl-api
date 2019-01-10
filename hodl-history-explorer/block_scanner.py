#!/usr/bin/env python3
# written by patrick hennis

import bitcoin
import bitcoin.rpc
from conf.coin import CoinParams
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("--height", help="set block height to start scan at")
args = parser.parse_args()

bitcoin.params = bitcoin.core.coreparams = CoinParams()
proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)


if args.height:
    height = args.height
else:
    height = 1

block = proxy.call('getblock', str(height))

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
                            with open('data.txt', 'a') as f:
                                addrs = []
                                for v in vout:
                                    if 'addresses' in v['scriptPubKey']:
                                        if v['scriptPubKey']['addresses'][0][0] == 'b':
                                            amount = vout[0]['value']
                                        addrs.append(v['scriptPubKey']['addresses'])
                                data = {'txid': tx, 'height': block['height'], 'addresses': addrs, 'amount': amount}
                                f.write(str(data))
                                f.write("\n")
                            f.close()
                    except Exception as e:
                        pass
        height = int(height) + 1
        block = proxy.call('getblock', str(height))
    else:
        print("sleeping")
        time.sleep(60)
