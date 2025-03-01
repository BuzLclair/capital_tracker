import os

import pandas as pd
from datetime import datetime

from src.plutus_lens.data import collection_config


RAW_DATA_PATH = os.environ.get("capital_tracker_raw_data")
DATA_PATH = f'{RAW_DATA_PATH}/ibkr/ibkr_data.xlsx'




def cash_flow_prep(path):
    ''' Extract the cash flows positions from account activity data and returns a cleaned df.

    Returns
    -------
    cash_flows : DataFrame
        Cleaned cash flows df.

    '''

    data = pd.read_excel(path, sheet_name='cash_flows')
    data = data.loc[data['Currency'] != 'Total']
    data['Settle Date'] = pd.to_datetime(data['Settle Date'])
    data['platform'] = 'Interactive Brokers'
    data['type'] = 'Transfer'
    data['subtype'] = 'Variable'
    data['asset_class'] = 'Cash'
    data.rename(columns={'Currency':'currency', 'Settle Date': 'date', 'Description': 'description', 'Amount': 'amount'}, inplace=True)
    return data[['date', 'type', 'subtype', 'amount', 'platform', 'currency', 'description', 'asset_class']]



def securities_ledger_prep(path):
    ''' Extract the securities movements from account activity data and returns a cleaned df.

    Returns
    -------
    secu_ledger : DataFrame
        Cleaned df with the securities transactions.

    '''

    securities_transactions = pd.read_excel(path, sheet_name='ibkr_secu_flow')

    secu_ledger = securities_transactions.loc[:, ('Date/Time', 'Symbol', 'Quantity', 'Currency', 'Asset Category', 'Comm/Fee', 'T. Price', 'Proceeds')].copy()
    secu_ledger.rename(columns={'Date/Time':'date', 'Symbol':'ticker', 'Quantity':'units', 'Currency':'quote_currency', 'Comm/Fee':'fees', 'T. Price':'amount', 'Asset Category':'asset_class'}, inplace=True)
    secu_ledger['date'] = secu_ledger['date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d, %H:%M:%S'))
    secu_ledger['units'] = secu_ledger['units'].str.replace(',','').astype(float)

    secu_ledger.loc[:, 'platform'] = 'Interactive Brokers'
    secu_ledger.loc[secu_ledger['asset_class']=='Stocks', 'asset_class'] = 'Equity'
    secu_ledger.loc[secu_ledger['Proceeds']<0, 'type'] = 'buy'
    secu_ledger.loc[secu_ledger['Proceeds']>=0, 'type'] = 'sell'
    secu_ledger.loc[secu_ledger['type']=='sell', 'units'] *= -1
    secu_ledger.loc[secu_ledger['type']=='buy', 'amount'] *= -1
    return secu_ledger



def fx_balancing(secu_ledger):
    ''' Creates an entry in the cash_flows collection at each stock buy / sell to settle the trades and rebalance the amount of each sub-portfolios.

    Parameters
    ----------
    secu_ledger : DataFrame
        list of all the securities transactions.

    '''

    forex_transactions = secu_ledger.loc[secu_ledger['asset_class']=='Forex'][['date', 'platform', 'type', 'ticker', 'units', 'Proceeds', 'fees', 'quote_currency']].copy()
    forex_transactions.rename(columns={'quote_currency':'currency', 'Proceeds':'amount'}, inplace=True)
    forex_transactions['ticker'] = forex_transactions['ticker'].str.split('.', expand=True).iloc[:,0]
    forex_transactions['asset_class'] = 'Cash'
    forex_transactions['description'] = forex_transactions['type'] + ' ' + forex_transactions['units'].astype(str) + ' ' + forex_transactions['ticker'] + ' with ' + forex_transactions['currency']

    fx_leg1 = forex_transactions.copy()
    fx_leg1['amount'] += fx_leg1['fees']
    fx_leg1 = fx_leg1[['date', 'type', 'amount', 'platform', 'currency', 'description', 'asset_class']]

    fx_leg2 = forex_transactions.copy()
    fx_leg2['temp_currency'] = fx_leg2['ticker']
    fx_leg2['ticker'] = fx_leg2['currency']
    fx_leg2['currency'] = fx_leg2['temp_currency']
    fx_leg2['amount'] = fx_leg2['units']
    fx_leg2 = fx_leg2[['date', 'type', 'amount', 'platform', 'currency', 'description', 'asset_class']]

    fx_transactions = pd.concat([fx_leg1, fx_leg2], ignore_index=True)
    fx_transactions['type'] = 'Transfer'
    fx_transactions['subtype'] = 'Variable'
    return fx_transactions



def cash_balancing(secu_ledger):
    ''' Creates an entry in the cash_flows collection at each stock buy / sell to settle the trades and rebalance the amount of each sub-portfolios.

    Parameters
    ----------
    secu_ledger : DataFrame
        list of all the securities transactions.

    '''

    cash_rebalance = secu_ledger[['Proceeds', 'fees', 'platform', 'date', 'type', 'ticker', 'units', 'quote_currency']].copy()
    cash_rebalance['amount'] = (1*(cash_rebalance['type']=='buy') - 1*(cash_rebalance['type']=='sell')) * cash_rebalance['Proceeds'] + cash_rebalance['fees']
    cash_rebalance['asset_class'] = 'Cash'
    cash_rebalance.rename(columns={'quote_currency':'currency'}, inplace=True)
    cash_rebalance['type'] = 'Transfer'
    cash_rebalance['description'] = cash_rebalance['type'] + ' ' + cash_rebalance['units'].astype(str) + ' units of ' + cash_rebalance['ticker']
    cash_rebalance['subtype'] = 'Variable'
    return cash_rebalance[['date', 'type', 'subtype', 'amount', 'platform', 'currency', 'description', 'asset_class']]



def dividends_prep(path):
    ''' Creates an entry in the cash_flows collection for each dividend. '''

    dividends = pd.read_excel(path, sheet_name='ibkr_dividends')
    dividends = dividends.loc[~dividends['Currency'].str.contains('Total'), ('Date', 'Amount', 'Currency', 'Description')]
    dividends.rename(columns={'Date':'date', 'Amount':'amount', 'Currency':'currency', 'Description':'description'}, inplace=True)

    dividends['date'] = pd.to_datetime(dividends['date'])
    dividends['type'] = 'Inflow'
    dividends['subtype'] = 'Variable'
    dividends['platform'] = 'Interactive Brokers'
    dividends['asset_class'] = 'Cash'
    return dividends[['date', 'type', 'subtype', 'amount', 'platform', 'currency', 'description', 'asset_class']]






def main():
    secu_ledger = securities_ledger_prep(DATA_PATH)
    secu_ledger_filtered = secu_ledger.loc[secu_ledger['asset_class']=='Equity']

    cash_flows = collection_config(dataframe=cash_flow_prep(DATA_PATH), collection_name='collection_cash_flows')
    fx_transactions = collection_config(dataframe=fx_balancing(secu_ledger), collection_name='collection_cash_flows')
    securities_ledger = collection_config(
        dataframe=secu_ledger_filtered[['date', 'type', 'units', 'platform', 'ticker', 'quote_currency', 'asset_class', 'fees', 'amount']],
        collection_name='collection_securities_ledger', amount_col='units', ccy_col='quote_currency')
    cash_balanc = collection_config(dataframe=cash_balancing(secu_ledger_filtered), collection_name='collection_cash_flows')
    dividends = collection_config(dataframe=dividends_prep(DATA_PATH), collection_name='collection_cash_flows')

    dfs_list = [cash_flows, fx_transactions, securities_ledger, cash_balanc, dividends]
    return dfs_list









if __name__ == '__main__':
    test = main()
