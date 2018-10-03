#!/usr/bin/env python3
from bitcoin.core import b2x, x, lx, CTransaction, CScript
from binascii import unhexlify
import binascii

# get op_return from transaction
tx_hex_string = '010000000195872154854064bf78e6fca1f43b67aac4aa95f440f56373e5e02fdcfa4c64c4020000006a473044022000aaae1500a73d4ecdb466e147363ca2ec5a3eb886ab4f9dca383498944f91cf02206fb0100db280cbd83e6769d7cf6dedd30b33e2f818fffe9e1a277c84d51e43300121030efdba03bfd0a6183fa9bf0d0309f0f268b2ad71ba2805c2b735e423af7d3804ffffffff0340420f000000000017a914a09cdcaacedee8a8813fee25185c8ed1b1b06d87870000000000000000656a4c6252454445454d2053435249505420303439663263303235636231373532313033306566646261303362666430613631383366613962663064303330396630663236386232616437316261323830356332623733356534323361663764333830346163a05eba05000000001976a914e33115988e5b84d5a5d5dfb633bc6ef46715282388ac00000000'
hex = unhexlify(tx_hex_string)
deserializedTransaction = CTransaction.deserialize(hex)
op_return_vout = deserializedTransaction.vout[1].scriptPubKey

# get redeem script
redeem_script = ''
for i in op_return_vout:
    script = bytes(i).decode('utf8')
    if 'REDEEM' in script:
        redeem_script_string = script.replace('REDEEM SCRIPT ', '')
print("Redeem script:", redeem_script_string)

# get nlocktime
redeemScript = CScript(unhexlify(redeem_script_string))
redeem_script_array = []
for i in redeemScript:
    redeem_script_array.append(i)
nlocktime_hex = b2x(lx(b2x(redeem_script_array[0])))
nlocktime = int(nlocktime_hex, 16)
print("nLockTime:", nlocktime)
