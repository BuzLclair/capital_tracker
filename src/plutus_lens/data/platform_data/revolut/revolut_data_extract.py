import os
import pandas as pd

from datetime import datetime
from src.plutus_lens.data import collection_config




RAW_DATA_PATH = os.environ.get("capital_tracker_raw_data")
STATEMENT_PATH_ROOT = f'{RAW_DATA_PATH}/revolut'
DATA_PATHS = {
    'current_account':f'{STATEMENT_PATH_ROOT}/account_statement_data/',
    'cryptos':f'{STATEMENT_PATH_ROOT}/crypto_data/',
    'previous_account':f'{STATEMENT_PATH_ROOT}/transactions_history.csv',
    'money_market':f'{STATEMENT_PATH_ROOT}/saving_data/',
}



def clean_account_statement(path_current_account, path_previous_account):
    ''' Get and clean the data in the Account Activity excel sheet.

    Returns
    -------
    df : DataFrame
        Cleaned df with proper columns formatting.

    '''

    account_statements_list = os.listdir(path_current_account)
    account_statements_list_filtered = list(filter(lambda x: '.csv' in x, account_statements_list))
    account_statements_files = [pd.read_csv(path_current_account + file)[['Type', 'Completed Date', 'Description', 'Amount', 'Fee', 'Currency', 'Balance', 'State']] for file in account_statements_list_filtered]

    df = pd.concat(account_statements_files, ignore_index=True)
    df = df.loc[df['State'] == 'COMPLETED']
    df['Amount'] -= df['Fee']
    df1 = pd.read_csv(path_previous_account)
    df1 = df1.loc[df1['State'] == 'Completed'][df.columns]
    df1['Amount'] += df1['Fee']
    merged_df = pd.concat([df, df1], ignore_index=True)
    merged_df['Completed Date'] = pd.to_datetime(merged_df['Completed Date'])
    return merged_df



def convert_english_months(df_col):
    month_translation = {'janv.': 'Jan', 'févr.': 'Feb', 'mars': 'Mar', 'avr.': 'Apr', 'mai': 'May', 'juin': 'Jun',
    'juil.': 'Jul', 'août': 'Aug', 'sept.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'déc.': 'Dec'}
    for fr, en in month_translation.items():
        df_col = df_col.str.replace(fr, en)
    return df_col


def cash_flow_prep(path_current_account, path_previous_account):
    ''' Extract the cash flows positions from account activity data and returns a cleaned df.

    Returns
    -------
    cash_flows : DataFrame
        Cleaned cash flows df.

    '''

    cash_flows = clean_account_statement(path_current_account, path_previous_account)
    cash_flows.loc[:, 'platform'] = 'Revolut'

    in_out_mask = (cash_flows['Type'].isin(['EXCHANGE', 'TOPUP', 'TRANSFER'])) | ((cash_flows['Type'] == 'REFUND') & (cash_flows['Description'].str.contains('Transfer', na=False)))
    cash_flows.loc[in_out_mask & (cash_flows['Description'].str.replace('From ', '').str.upper() == cash_flows['Description'].str.replace('From ', '')), ('type', 'subtype')] = ['Transfer', 'Variable']
    cash_flows.loc[in_out_mask & (cash_flows['Description'].str.replace('To ', '').str.upper() == cash_flows['Description'].str.replace('To ', '')), ('type', 'subtype')] = ['Outflow', 'Variable']
    cash_flows.loc[in_out_mask & (cash_flows['Description'].str.replace('From ', '').str.upper() != cash_flows['Description'].str.replace('From ', '')), ('type', 'subtype')] = ['Transfer', 'Variable']
    cash_flows.loc[in_out_mask & (cash_flows['Description'].str.replace('To ', '').str.upper() != cash_flows['Description'].str.replace('To ', '')), ('type', 'subtype')] = ['Transfer', 'Variable']
    cash_flows.loc[cash_flows['Description'].str.contains('Top-Up'), ('type', 'subtype')] = ['Transfer', 'Variable']
    cash_flows.loc[(cash_flows['Description'].str.contains('Exchanged to') | cash_flows['Description'].str.contains('Exchanged from')), ('type', 'subtype')] = ['Transfer', 'Variable']
    cash_flows.loc[cash_flows['type'] != cash_flows['type'], 'type'] = 'Outflow'
    cash_flows.loc[cash_flows['subtype'] != cash_flows['subtype'], 'subtype'] = 'Variable'

    cash_flows = cash_flows.loc[:, ('Completed Date', 'type', 'subtype', 'Amount', 'platform', 'Currency', 'Description')]
    cash_flows.columns = ['date', 'type', 'subtype', 'amount', 'platform', 'currency', 'description']
    cash_flows['asset_class'] = 'Cash'
    return cash_flows




def __add_transfer_fees(crypto_ledger):
    ''' Add a row in the crypto ledger df each time there is a transaction to account for the fees. '''

    filter_ledger = crypto_ledger.loc[crypto_ledger['type']=='transfer out'].copy()
    filter_ledger['units'] = filter_ledger['fees'] / filter_ledger['price']
    filter_ledger['type'] = 'transfer fees'
    crypto_ledger = pd.concat([crypto_ledger, filter_ledger], ignore_index=True)
    return crypto_ledger


def cryptos_prep(path_cryptos):
    ''' Extract the cryptos transactions from the dedicated csv, returns a cleaned df and feeds it into the MongoDB database. '''

    crypto_ledger_list = os.listdir(path_cryptos)
    crypto_ledger_list_filtered = list(filter(lambda x: '.csv' in x, crypto_ledger_list))
    crypto_ledger_list_files = [pd.read_csv(path_cryptos + file) for file in crypto_ledger_list_filtered]

    crypto_ledger = pd.concat(crypto_ledger_list_files, ignore_index=True)
    # crypto_ledger = pd.read_csv(path_cryptos)
    crypto_ledger['Date'] = convert_english_months(crypto_ledger['Date'])
    crypto_ledger['Date'] = crypto_ledger['Date'].apply(lambda x: datetime.strptime(x, '%d %b %Y, %H:%M:%S'))
    crypto_ledger['currency'] = crypto_ledger['Fees'].str.split(' ', expand=True).iloc[:,-1]
    crypto_ledger[['Quantity', 'Price', 'Value', 'Fees']] = crypto_ledger[['Quantity', 'Price', 'Value', 'Fees']].replace({',':'.', 'CHF':'', ' ':'', ' ':''}, regex=True).astype(float)
    crypto_ledger.rename(columns={'Quantity':'units', 'Value':'amount', 'Fees':'fees', 'Date':'date', 'Symbol':'ticker', 'Type':'type', 'Price':'price'}, inplace=True)

    crypto_ledger['platform'] = 'Revolut'
    crypto_ledger.loc[crypto_ledger['type']=='Achat', 'type'] = 'buy'
    crypto_ledger.loc[crypto_ledger['type']=='Vente', 'type'] = 'sell'
    crypto_ledger.loc[crypto_ledger['type']=='Envoi', 'type'] = 'transfer out'
    crypto_ledger.loc[(crypto_ledger['type']=='sell') | (crypto_ledger['type']=='transfer out'), 'units'] *= -1
    crypto_ledger.loc[(crypto_ledger['type']=='buy'), 'amount'] *= -1
    crypto_ledger['fees'] *= -1
    crypto_ledger.loc[(crypto_ledger['type']=='buy') | (crypto_ledger['type']=='sell'), 'units'] += crypto_ledger['fees'] / crypto_ledger['price']
    crypto_ledger['asset_class'] = 'Cryptos'
    crypto_ledger['ticker'] += '-USD'

    crypto_ledger = __add_transfer_fees(crypto_ledger)
    return crypto_ledger[['date', 'type', 'units', 'platform', 'ticker', 'currency', 'asset_class', 'amount', 'fees', 'price']]



def money_market_prep(path_money_market):
    ''' Extract the money market funds transactions from the dedicated csv, returns a cleaned df and feeds it into the MongoDB database. '''

    money_market_list = os.listdir(path_money_market)
    money_market_list_list_filtered = list(filter(lambda x: '.csv' in x, money_market_list))
    money_market_list_list_files = [pd.read_csv(path_money_market + file) for file in money_market_list_list_filtered]

    money_market_df = pd.concat(money_market_list_list_files, ignore_index=True)
    money_market_df['Date'] = convert_english_months(money_market_df['Date'])
    money_market_df['Date'] = money_market_df['Date'].apply(lambda x: datetime.strptime(x, '%d %b %Y, %H:%M:%S'))

    currencies = {'£': 'GBP', '€': 'EUR', 'CHF': 'CHF'}
    for ccy, currency_code in currencies.items():
        mask = money_market_df['Value'].str.contains(ccy)
        money_market_df.loc[mask, 'currency'] = currency_code
        money_market_df.loc[mask, 'Value'] = money_market_df.loc[mask, 'Value'].str.replace(ccy, '')

    money_market_df.rename(columns={'Value':'amount', 'Date':'date', 'Description':'description'}, inplace=True)
    money_market_df['amount'] = money_market_df['amount'].astype(float)
    money_market_df['platform'] = 'Revolut'

    money_market_df.loc[money_market_df['description'].str.contains('BUY'), 'type'] = 'buy'
    money_market_df.loc[money_market_df['description'].str.contains('Service Fee'), 'type'] = 'fees'
    money_market_df.loc[money_market_df['description'].str.contains('Interest'), 'type'] = 'interest'

    money_market_df['isin'] = money_market_df['description'].str.split(' ').str[-1]
    money_market_df['asset_class'] = 'Fixed income'
    return money_market_df[['date', 'type', 'platform', 'isin', 'currency', 'asset_class', 'amount', 'description']]



def main():
    crypto_ledger = cryptos_prep(DATA_PATHS['cryptos'])

    cash_flows = collection_config(
        dataframe=cash_flow_prep(DATA_PATHS['current_account'], DATA_PATHS['previous_account']), collection_name='collection_cash_flows')
    cryptos = collection_config(dataframe=crypto_ledger, collection_name='collection_cryptos', amount_col='units')
    money_market = collection_config(dataframe=money_market_prep(DATA_PATHS['money_market']), collection_name='collection_fixed_income', amount_col='amount')

    dfs_list = [cash_flows, cryptos, money_market]
    return dfs_list



if __name__ == '__main__':
    test = main()
