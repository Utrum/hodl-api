#!/usr/bin/env python3

import bitcoin
import bitcoin.rpc
import binascii, array
from conf.coin import CoinParams

bitcoin.params = bitcoin.core.coreparams = CoinParams()

proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)


# get first block
hash = proxy.getblockhash(0)
print(hash)
block = proxy.getblock(hash)
