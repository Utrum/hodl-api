#!/usr/bin/env python3
# Copyright (C) 2015 Peter Todd <pete@petertodd.org>
#
# This file is subject to the license terms in the LICENSE file found in the
# top-level directory of this distribution.

import argparse
import binascii
import bitcoin
import bitcoin.rpc
import logging
import math

from bitcoin.core import (
        b2x, b2lx, lx, x,
        str_money_value, COIN,
        COutPoint, CTxIn, CTxOut, CTransaction
)
from bitcoin.core.script import (
        OP_NOP2, OP_DROP, OP_CHECKSIG,
        CScript
)
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

parser = argparse.ArgumentParser(
    description="hodl your bitcoins with CHECKLOCKTIMEVERIFY")
parser.add_argument('-v', action='store_true', dest='verbose', help='Verbose')
parser.add_argument('pubkey', action='store', help='Public key')
parser.add_argument('nLockTime', action='store', type=int, help='nLockTime')
subparsers = parser.add_subparsers(
    title='Subcommands',
    description='All operations are done through subcommands:')


def hodl_redeemScript(pubKey, nLockTime):
    pubkey = CPubKey(x(pubKey))
    return CScript([nLockTime, OP_NOP2, OP_DROP, pubkey, OP_CHECKSIG])


# ----- create -----
parser_create = subparsers.add_parser(
        'create',
        help='Create an address for hodling')


def create_command(args):
    redeemScript = hodl_redeemScript(args.pubkey, args.nLockTime)
    logging.debug('redeemScript: %s' % b2x(redeemScript))

    addr = P2SHBitcoinAddress.from_redeemScript(redeemScript)
    print(addr)
    print(b2x(redeemScript))

parser_create.set_defaults(cmd_func=create_command)


# ----- spend -----
parser_spend = subparsers.add_parser(
    'spend', help='Spend (all) your hodled coins')
parser_spend.add_argument(
    'prevouts', nargs='+', metavar='txid:n', help='Transaction output')
parser_spend.add_argument(
    'addr', action='store', help='Address to send the funds too')


def spend_command(args):
    args.addr = CBitcoinAddress(args.addr)
    redeemScript = hodl_redeemScript(args.pubkey, args.nLockTime)
    scriptPubKey = redeemScript.to_p2sh_scriptPubKey()
    proxy = bitcoin.rpc.Proxy(btc_conf_file=bitcoin.params.CONF_FILE)
    prevouts = []
    for prevout in args.prevouts:
        try:
            txid, n = prevout.split(':')
            txid = lx(txid)
            n = int(n)
            outpoint = COutPoint(txid, n)
        except ValueError:
            args.parser.error('Invalid output: %s' % prevout)
        try:
            prevout = proxy.gettxout(outpoint)
        except IndexError:
            args.parser.error('Outpoint %s not found' % outpoint)
        prevout = prevout['txout']
        if prevout.scriptPubKey != scriptPubKey:
            args.parser.error('Outpoint not correct scriptPubKey')
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
        [CTxOut(sum_in - fees, args.addr.to_scriptPubKey())],
        args.nLockTime)

    ready_to_sign_tx = CTransaction(
        [CTxIn(
            txin.prevout,
            redeemScript,
            nSequence=0)
            for i, txin in enumerate(unsigned_tx.vin)],
        unsigned_tx.vout,
        unsigned_tx.nLockTime)

    print(b2x(ready_to_sign_tx.serialize()))

parser_spend.set_defaults(cmd_func=spend_command)

args = parser.parse_args()
args.parser = parser

if args.verbose:
    logging.root.setLevel('DEBUG')

if not hasattr(args, 'cmd_func'):
    parser.error('No command specified')

args.cmd_func(args)
