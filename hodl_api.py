#!/usr/bin/env python3

import bitcoin.rpc
from bitcoin.core import (
        b2x, b2lx, lx, x, COIN, COutPoint, CTxIn, CTxOut, CTransaction)
from bitcoin.core.script import (
        OP_NOP2, OP_DROP, OP_CHECKSIG, OP_RETURN, CScript)
from bitcoin.core.key import CPubKey
from bitcoin.wallet import P2SHBitcoinAddress, CBitcoinAddress


class KomodoParams(bitcoin.core.CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    RPC_PORT = 7771
    CONF_FILE = "/volumes/assetchains/OOT/OOT.conf"
    DNS_SEEDS = (('seeds.komodoplatform.com', 'static.kolo.supernet.org'))
    BASE58_PREFIXES = {'PUBKEY_ADDR': 60,
                       'SCRIPT_ADDR': 85,
                       'SECRET_KEY': 188}

bitcoin.params = bitcoin.core.coreparams = KomodoParams()


def hodl_redeemScript(pubkey, nLockTime):
    publicKey = CPubKey(x(pubkey))
    return CScript([nLockTime, OP_NOP2, OP_DROP, publicKey, OP_CHECKSIG])


def create_command(pubkey, nLockTime):
    redeemScript = hodl_redeemScript(pubkey, nLockTime)

    addr = P2SHBitcoinAddress.from_redeemScript(redeemScript)
    print(addr)
    print(b2x(redeemScript))


def spend_command(pubkey, nLockTime, prevOuts, addr):
    address = CBitcoinAddress(addr)
    redeemScript = hodl_redeemScript(pubkey, nLockTime)
    scriptPubKey = redeemScript.to_p2sh_scriptPubKey()
    proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)
    prevouts = []
    for prevout in prevOuts:
        try:
            txid, n = prevout.split(':')
            txid = lx(txid)
            n = int(n)
            outpoint = COutPoint(txid, n)
        except ValueError:
            print('Invalid output: %s' % prevout)
        try:
            prevout = proxy.gettxout(outpoint)
        except IndexError:
            print('Outpoint %s not found' % outpoint)
        prevout = prevout['txout']
        if prevout.scriptPubKey != scriptPubKey:
            print('Outpoint not correct scriptPubKey')
        prevouts.append((outpoint, prevout))

    sum_in = sum(prev_txout.nValue for outpoint, prev_txout in prevouts)

    tx_size = (4 +  # version field
               2 +  # number of txins
               len(prevouts) * 153 +  # txins, including sigs
               1 +  # number of txouts
               34 +  # txout
               4)  # nLockTime field

    feerate = int(proxy._call('estimatefee', 1) * COIN)  # satoshi's per KB
    if feerate <= 0:
        feerate = 10000
    fees = int(tx_size / 1000 * feerate)

    unsigned_tx = CTransaction(
        [CTxIn(outpoint, nSequence=0) for outpoint, prevout in prevouts],
        [
            CTxOut(sum_in - fees, address.to_scriptPubKey()),
            CTxOut(
                0,
                CScript([OP_RETURN, ('DEPOSITS UNLOCKED').encode()])
            )
        ],
        nLockTime)

    ready_to_sign_tx = CTransaction(
        [CTxIn(
            txin.prevout,
            redeemScript,
            nSequence=0)
            for i, txin in enumerate(unsigned_tx.vin)],
        unsigned_tx.vout,
        unsigned_tx.nLockTime)

    print(b2x(ready_to_sign_tx.serialize()))
