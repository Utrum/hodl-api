#!/usr/bin/env python3

import bitcoin
import bitcoin.rpc
from conf.coin import CoinParams

bitcoin.params = bitcoin.core.coreparams = CoinParams()

proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)


# get first block
block = proxy.call('getblock', str(0))
print(block)
