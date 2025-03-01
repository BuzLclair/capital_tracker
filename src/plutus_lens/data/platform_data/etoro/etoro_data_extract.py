import os
import pandas as pd

from src.plutus_lens.data import collection_config


RAW_DATA_PATH = os.environ.get("capital_tracker_raw_data")
DATA_PATH = f'{RAW_DATA_PATH}/etoro/account_statement_data/'
TICKERS_CORR_PATH = r'C:/Users/const/Documents/Code/Python/PlutusForge/plutus-lens/src/plutus_lens/services/ticker_corr.xlsx'



class EtoroData:

    def __init__(self, data_path):
        self.data_path = data_path
        self.account_activity_df = self.clean_account_activity()
        self.cash_flows = self.cash_flow_prep()
        self.secu_ledger = self.securities_ledger_prep()
        self.cash_rebalance = self.cash_balancing()


    def clean_account_activity(self):
        ''' Get and clean the data in the Account Activity excel sheet.

        Returns
        -------
        df : DataFrame
            Cleaned df with proper columns formatting.

        '''

        account_statements_list = os.listdir(self.data_path)
        account_statements_list_filtered = list(filter(lambda x: '.xlsx' in x, account_statements_list))
        account_statements_files = [pd.read_excel(self.data_path + file, sheet_name='Account Activity') for file in account_statements_list_filtered]

        account_activity_df = pd.concat(account_statements_files, ignore_index=True)
        account_activity_df['Date'] = pd.to_datetime(account_activity_df['Date'], dayfirst=True)
        return account_activity_df


    def cash_flow_prep(self):
        ''' Extract the cash flows positions from account activity data and returns a cleaned df.

        Returns
        -------
        cash_flows : DataFrame
            Cleaned cash flows df.

        '''

        cash_flows_rows = self.account_activity_df[self.account_activity_df['Type'] == 'Deposit'].copy()
        cash_flows = cash_flows_rows.loc[:, ('Date', 'Type', 'Amount')].copy()
        cash_flows.columns = ['date', 'type', 'amount']
        cash_flows.loc[:, 'platform'] = 'Etoro'
        cash_flows.loc[:, 'currency'] = cash_flows_rows.loc[:,'Details'].str.split(' ').str[1]
        cash_flows['asset_class'] = 'Cash'
        cash_flows['type'] = 'Transfer'
        cash_flows['subtype'] = 'Variable'
        cash_flows['description'] = 'Cash deposit'
        return cash_flows


    def securities_ledger_prep(self):
        ''' Extract the securities movements from account activity data and returns a cleaned df.

        Returns
        -------
        secu_ledger : DataFrame
            Cleaned df with the securities transactions.

        '''

        securities_transactions = self.account_activity_df.loc[self.account_activity_df['Type'].isin(['Open Position', 'Position closed'])]

        secu_ledger = securities_transactions.loc[:, ('Date', 'Type', 'Details', 'Units', 'Asset type', 'Amount')].copy()
        secu_ledger.loc[:, 'platform'] = 'Etoro'
        secu_ledger.loc[:, 'Asset type'] = 'Equity'
        secu_ledger[['ticker', 'quote_currency']] = secu_ledger['Details'].str.split('/', expand=True)
        secu_ledger.loc[secu_ledger['Type']=='Open Position', 'Type'] = 'buy'
        secu_ledger.loc[secu_ledger['Type']=='Position closed', 'Type'] = 'sell'
        secu_ledger['quote_currency'] = secu_ledger['quote_currency'].str.replace('GBX', 'GBP', regex=False)
        secu_ledger['ticker'] = self._tickers_list_update(TICKERS_CORR_PATH, secu_ledger['ticker'].to_list(), col_to_corr='etoro_ticker', col_to_keep='yf_ticker')

        secu_ledger.drop(columns=['Details'], inplace=True)
        secu_ledger.rename(columns={'Type':'type', 'Date':'date', 'Units':'units', 'Asset type':'asset_class'}, inplace=True)
        secu_ledger['units'] = secu_ledger['units'].astype(float)
        secu_ledger.loc[secu_ledger['type']=='sell', 'units'] *= -1
        return secu_ledger


    def stock_split_corr(self, securities_ledger):
        ''' Adds simulated quantity to a stock following a stock split to adjust the owned quantity.

        Parameters
        ----------
        securities_ledger : DataFrame
            list of all the stock transactions, used to know the owned wuantity of a stock at the split.

        '''

        split_events_raw = self.account_activity_df.loc[self.account_activity_df['Type'] == 'corp action: Split'].copy()
        split_events = split_events_raw[['Date', 'Details', 'Asset type']]
        split_events.loc[:, ('ticker', 'splitter')] = split_events['Details'].str.split(' ', expand=True).values
        splits_adj = pd.DataFrame(columns=['date', 'type', 'units', 'platform', 'ticker', 'quote_currency', 'asset_class'], dtype='object')
        for idx, split in split_events.iterrows():
            ticker = split['ticker'].split('/')[0]
            owned_qt = securities_ledger.loc[(securities_ledger['date']<=split['Date']) & (securities_ledger['ticker'] == ticker)]['units']
            if sum(owned_qt) != 0:
                adjustment = sum(owned_qt) * int(split['splitter'].split(':')[0]) / int(split['splitter'].split(':')[1])
                adjustment -= sum(owned_qt) # this qt is already owned, no need to adjust for this
                adjusted_row = {'date':split['Date'], 'type':'split adjustment', 'units':adjustment, 'platform':'Etoro', 'ticker':ticker, 'quote_currency':split['ticker'].split('/')[1], 'asset_class':'Equity'}
                splits_adj.loc[len(splits_adj)] = adjusted_row
        splits_adj.index = range(len(securities_ledger), len(securities_ledger)+len(splits_adj))
        return splits_adj


    def cash_balancing(self):
        ''' Creates an entry in the cash_flows collection at each stock buy / sell to settle the trades and rebalance the amount of each sub-portfolios.

        Parameters
        ----------
        secu_ledger : DataFrame
            list of all the securities transactions.

        '''

        secu_ledger = self.secu_ledger.copy()

        cash_rebalance = secu_ledger[['Amount', 'platform', 'date', 'type', 'ticker', 'units']].copy()
        cash_rebalance['currency'] = 'USD'
        cash_rebalance['asset_class'] = 'Cash'
        cash_rebalance.rename(columns={'Amount':'amount'}, inplace=True)
        cash_rebalance.loc[cash_rebalance['type']=='buy', 'amount'] *= -1
        cash_rebalance['description'] = cash_rebalance['type'] + ' ' + cash_rebalance['units'].astype(str) + ' units of ' + cash_rebalance['ticker']
        cash_rebalance['type'] = 'Transfer'
        cash_rebalance['subtype'] = 'Variable'
        cash_rebalance = cash_rebalance[['date', 'type', 'subtype', 'amount', 'platform', 'currency', 'description', 'asset_class']]
        return cash_rebalance


    def dividends_prep(self):
        ''' Creates an entry in the cash_flows collection for each dividend. '''

        dividends = self.account_activity_df.loc[self.account_activity_df['Type'] == 'Dividend']
        dividends = dividends.loc[:, ('Date', 'Type', 'Details', 'Amount')].copy()
        dividends.rename(columns={'Type':'type', 'Date':'date', 'Amount':'amount'}, inplace=True)

        dividends[['ticker', 'currency']] = dividends['Details'].str.split('/', expand=True)
        dividends['ticker'] = self._tickers_list_update(TICKERS_CORR_PATH, dividends['ticker'].to_list(), col_to_corr='etoro_ticker', col_to_keep='yf_ticker')
        dividends['currency'] = dividends['currency'].str.replace('GBX', 'GBP', regex=False)

        dividends['description'] = dividends['ticker'] + ' Cash Dividend ' + dividends['currency'] + ' ' + dividends['amount'].astype(str)

        dividends['type'] = 'Inflow'
        dividends['subtype'] = 'Variable'
        dividends['platform'] = 'Etoro'
        dividends['asset_class'] = 'Cash'
        return dividends[['date', 'type', 'subtype', 'amount', 'platform', 'currency', 'description', 'asset_class']]


    @staticmethod
    def _tickers_list_update(ticker_path, tickers_list, col_to_corr, col_to_keep):
        ''' For a given list of tickers, update it with the corrected tickers readable by yahoo finance or the db. '''

        ticker_corr = pd.read_excel(ticker_path)
        ticker_corr_map = dict(zip(ticker_corr[col_to_corr], ticker_corr[col_to_keep]))
        tickers_list = [ticker_corr_map.get(ticker, ticker) for ticker in tickers_list]
        tickers_list = [ticker.strip().upper() for ticker in tickers_list if not pd.isna(ticker)]
        return tickers_list




def main():
    etoro_data_object = EtoroData(DATA_PATH)

    secu_ledger = etoro_data_object.secu_ledger
    secu_ledger_filtered = secu_ledger[['date', 'type', 'units', 'platform', 'ticker', 'quote_currency', 'asset_class']]
    split_adjustment = etoro_data_object.stock_split_corr(secu_ledger_filtered)
    secu_ledger_filtered = pd.concat([secu_ledger_filtered, split_adjustment], ignore_index=True)

    cash_flows = collection_config(dataframe=etoro_data_object.cash_flows, collection_name='collection_cash_flows')
    cash_balanc = collection_config(dataframe=etoro_data_object.cash_rebalance, collection_name='collection_cash_flows')
    securities_ledger = collection_config(dataframe=secu_ledger_filtered, collection_name='collection_securities_ledger',
                                          amount_col='units', ccy_col='quote_currency')
    dividends = collection_config(dataframe=etoro_data_object.dividends_prep(), collection_name='collection_cash_flows')

    dfs_list = [cash_flows, cash_balanc, securities_ledger, dividends]
    return dfs_list





if __name__ == '__main__':
    etoro_data_object = EtoroData(DATA_PATH)
    test = main()
