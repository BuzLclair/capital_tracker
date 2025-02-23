import os
import time
import json

import pandas as pd
import requests
import urllib.parse
import hashlib
import hmac
import base64

from src.plutus_lens.data import collection_config





class KrakenAPI:

    def __init__(self):
        self.__api_key = os.environ.get('capital_tracker_kraken_key')
        self.__api_sec = os.environ.get('capital_tracker_kraken_sec')


    def get_kraken_signature(self, urlpath, data, secret):
        if isinstance(data, str):
            encoded = (str(json.loads(data)["nonce"]) + data).encode()
        else:
            encoded = (str(data["nonce"]) + urllib.parse.urlencode(data)).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()


    def kraken_api_prompt(self, url, data_offset):
        payload = json.dumps({
            'nonce': str(int(time.time()*1000)),
            'ofs':data_offset
        })
        sign_url = url.split('https://api.kraken.com')[-1]
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'API-Key': self.__api_key,
          'API-Sign': self.get_kraken_signature(sign_url, payload, self.__api_sec)
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()




def get_kraken_ledger_data(api_object, url, data_offset):
    kraken_ledger = api_object.kraken_api_prompt(url, data_offset)
    kraken_ledger_subset_df = pd.DataFrame(kraken_ledger['result']['ledger'].values())
    return kraken_ledger_subset_df



def get_full_kraken_ledger():
    api_object = KrakenAPI()
    url = 'https://api.kraken.com/0/private/Ledgers'

    kraken_ledger = api_object.kraken_api_prompt(url, 0)
    kraken_ledger_list = [pd.DataFrame(kraken_ledger['result']['ledger'].values())]

    ledger_size = kraken_ledger['result']['count']
    ledger_size -= 50
    data_offset = 50
    while ledger_size > 0:
        temp_ledger = get_kraken_ledger_data(api_object, url, data_offset)
        kraken_ledger_list.append(temp_ledger)
        ledger_size -= 50
        data_offset += 50

    kraken_ledger_df = pd.concat(kraken_ledger_list)
    return kraken_ledger_df




def clean_ledger(kraken_ledger_df):
    kraken_ledger_df['time'] = pd.to_datetime(kraken_ledger_df['time'], unit='s', utc=True)
    kraken_ledger_df[['amount', 'balance', 'fee']] = kraken_ledger_df[['amount', 'balance', 'fee']].astype(float)
    kraken_ledger_df['units'] = kraken_ledger_df['amount'] - kraken_ledger_df['fee']
    kraken_ledger_df['platform'] = 'Kraken'
    kraken_ledger_df.loc[kraken_ledger_df['asset'].isin(['ETH.F', 'XETH', 'ETH.B', 'XETH.F', 'XETH.B']), 'ticker'] = 'ETH'
    kraken_ledger_df.loc[kraken_ledger_df['asset'].isin(['SOL03.S', 'SOL']), 'ticker'] = 'SOL'
    kraken_ledger_df.loc[kraken_ledger_df['asset']=='EIGEN', 'ticker'] = 'EIGEN'

    kraken_ledger_df['asset_class'] = 'Cryptos'
    kraken_ledger_df['ticker'] += '-USD'
    kraken_ledger_df['currency'] = kraken_ledger_df['ticker']
    kraken_ledger_df[['amount', 'fee']] *= -1
    kraken_ledger_df.loc[kraken_ledger_df['type']=='deposit', 'type'] = 'transfer'

    kraken_ledger_df.rename(columns={'time':'date', 'fee':'fees'}, inplace=True)
    return kraken_ledger_df[['date', 'type', 'units', 'platform', 'ticker', 'currency', 'asset_class', 'amount', 'fees']]



def main():
    kraken_ledger_df = get_full_kraken_ledger()
    kraken_ledger_df = clean_ledger(kraken_ledger_df)

    cryptos = collection_config(dataframe=kraken_ledger_df, collection_name='collection_cryptos', amount_col='units')
    return [cryptos]
z = main()
