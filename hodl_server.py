#!/usr/bin/env python3
from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields
import hodl_api
import requests
import json

app = Flask(__name__, static_url_path="")
api = Api(app)


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

    def post(self, pubkey, nlocktime, addr):
        args = self.reqparse.parse_args()
        output = hodl_api.spend_command(
            pubkey=pubkey,
            nLockTime=nlocktime,
            prevOuts=args['prevouts'],
            addr=addr
        )
        return(output)

    def get(self, pubkey, nlocktime, addr):
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
            prevOuts=prevouts,
            addr=addr
        )
        return(output)


api.add_resource(Create, '/create/<pubkey>/<int:nlocktime>')
api.add_resource(Spend, '/spend/<pubkey>/<int:nlocktime>/<addr>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
