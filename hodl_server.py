#!/usr/bin/env python3
from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields
import hodl_api
import requests
import json
import time
from collections import deque

import random

# MIN_AMOUNT = 100
MIN_AMOUNT = 0.01  # TESTING!
# TOLERANCE_SEC = 43200
TOLERANCE_SEC = 60  # TESTING!
MAX_VEST_TIME = 120
MIN_VEST_TIME = 60

MIN_AMOUNT_SAT = MIN_AMOUNT * 100000000
# MAX_VEST_TIME_SEC = MAX_VEST_TIME * 86400
# MIN_VEST_TIME_SEC = MIN_VEST_TIME * 86400
MAX_VEST_TIME_SEC = 1800 # TESTING!
MIN_VEST_TIME_SEC = 900 # TESTING!

app = Flask(__name__, static_url_path="")
api = Api(app)

tx_queue = deque()
total = 0

class Create(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('pubkey', type=str, location='json')
        self.reqparse.add_argument('nlocktime', type=int, location='json')
        super(Create, self).__init__()

    def get(self, pubkey, nlocktime):
        output = hodl_api.create_command(pubkey=pubkey, nLockTime=nlocktime)
        return(output)


class Spend(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'prevouts',
            action='append',
            type=str,
            location='form'
        )
        super(Spend, self).__init__()

    def post(self, pubkey, nlocktime):
        args = self.reqparse.parse_args()
        output = hodl_api.spend_command(
            pubkey=pubkey,
            nLockTime=nlocktime,
            prevOuts=args['prevouts']
        )
        return(output)

    def get(self, pubkey, nlocktime):
        redeem_script = hodl_api.create_command(
            pubkey=pubkey,
            nLockTime=nlocktime
        )
        script_addr = redeem_script['address']

        url = hodl_api.CoinParams.EXPLORER
        url += '/insight-api-komodo/addr/' + script_addr + '/utxo'

        utxos = []
        try:
            r = requests.get(
                url,
                headers={'Content-type': 'text/plain; charset=utf-8'})
            utxos = json.loads(r.text)
        except Exception as e:
            print("Couldn't connect to " + url, e)

        prevouts = []
        for utxo in utxos:
            vout = str(utxo['vout'])
            prevouts.append(utxo['txid'] + ':' + vout)

        output = hodl_api.spend_command(
            pubkey=pubkey,
            nLockTime=nlocktime,
            prevOuts=prevouts
        )
        return(output)


class SubmitTx(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('rawtx', type=str, location='json')
        super(SubmitTx, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()

        # analyze transaction
        try:
            analysis = hodl_api.analyze_tx(args['rawtx'])
        except Exception as e:
            error_msg = "couldn't analyze this transaction"
            return({'error': error_msg, 'exception': str(e)})

        # check if it complies with minimum allowed locked amount
        if analysis['lockedSatoshis'] < MIN_AMOUNT_SAT:
            error_msg = 'minimum amount is ' + str(MIN_AMOUNT)
            return({'error': error_msg})

        # check if tx is not trying to get rewards for less than
        # the minimum allowed vesting period, or more than maximum
        nLockTime = analysis['nLockTime']
        now = int(time.time())
        min_unlock_time = now + MIN_VEST_TIME_SEC
        max_unlock_time = now + MAX_VEST_TIME_SEC
        if nLockTime < (min_unlock_time - TOLERANCE_SEC):
            error_msg = 'Code expired or vesting period is too short.'
            return({'error': error_msg})
        elif nLockTime > (max_unlock_time + MAX_VEST_TIME_SEC):
            error_msg = "You're hodling yourself out of existence!"
            return({'error': error_msg})
        elif nLockTime > (max_unlock_time + TOLERANCE_SEC):
            error_msg = 'Vesting period too long.'
            return({'error': error_msg})
        else:
            try:
                tx_broadcast_output = hodl_api.tx_broadcast(args['rawtx'])
            except Exception as e:
                print(e)
                error_msg = ("There was a problem " +
                    "broadcasting this transaction.")
                return({'error': error_msg})
            else:
                append_val = {}

                at = hodl_api.analyze_tx(args['rawtx'])
                append_val['address'] = at['authorizedAddress']
                append_val['rewards'] = 100000
                append_val['redeemScript'] = at['redeemScript']
                tx_queue.append(append_val)

                global total
                total += at['lockedSatoshis']

                return(tx_broadcast_output)


class Proccess(Resource):
    def __init__(self):
        super(Proccess, self).__init__()

    def findunspent(self):
        unspent = hodl_api.find_unspent()
        for tx in unspent:
            if tx['spendable'] == True:
                if tx['amount'] > total:
                    return str(tx['address'])

    def post(self):
        params = {}
        for tx in tx_queue:
            params[tx['address']] = tx['rewards']

        # todo:
        # create call to rpc proxy for sendmany, pass params containing addresses and reward amounts
        # after successful tx, empty tx_queue
        address = self.findunspent()
        results = hodl_api.sendmany_command(address, params)

        # returning params as temp return for now
        return(results)
        # return params

api.add_resource(Create, '/create/<pubkey>/<int:nlocktime>')
api.add_resource(Spend, '/spend/<pubkey>/<int:nlocktime>')
api.add_resource(SubmitTx, '/submit-tx/')
api.add_resource(Proccess, '/process/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
