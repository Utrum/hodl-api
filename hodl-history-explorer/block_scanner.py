#!/usr/bin/env python3

import bitcoin
import bitcoin.rpc
from conf.coin import CoinParams
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--height", help="increase output verbosity")
args = parser.parse_args()

bitcoin.params = bitcoin.core.coreparams = CoinParams()
proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)


if args.height:
    print("set output width to %s" % args.height)
    block = proxy.call('getblock', str(args.height))
else:
    # get first block
    block = proxy.call('getblock', str(0))

print(block)
