#!/usr/bin/env python3

import bitcoin
import bitcoin.rpc
from conf.coin import CoinParams

bitcoin.params = bitcoin.core.coreparams = CoinParams()

proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)


for i in range(10):
    hash = proxy.getblockhash(i)
    print(hash)
    print(hash.hex())
    block = proxy.getblock(hash)
