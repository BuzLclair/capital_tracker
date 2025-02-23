import pandas as pd

from src.plutus_lens.data import CollectionConnect
from src.plutus_lens.data.market_data.market_data_extract import ForexData



class CollectionService:
    ''' A class to interact with and process data from a MongoDB collection.

    It provides functionality to clean and analyze data, calculate balances,
    and organize information by platform and asset class.

    Attributes:
        main_collection (CollectionConnect): Connection to the main MongoDB collection.
        fx_data (DataFrame): Cleaned forex data for calculations.
        unit_of_account_col_name (str): Name of the column containing unit of account data.
        ticker_col_name (str): Name of the column containing ticker information.
        _date_range (DatetimeIndex): Range of dates for balance calculations.
        clean_data (DataFrame): Cleaned data from the main collection.
    '''

    def __init__(self, main_collection_name, unit_of_account_col_name, ticker_col_name):
        self.main_collection = CollectionConnect(database_name='capital_vault', collection_name=main_collection_name)
        self.fx_data = ForexData().clean_fx_data()
        self.unit_of_account_col_name = unit_of_account_col_name
        self.ticker_col_name = ticker_col_name
        self.cash_flows_data = CollectionConnect(database_name='capital_vault', collection_name='cash_flows').document_query({})
        self._date_range = pd.date_range(start=self.cash_flows_data['date'].min().normalize(), end=self.cash_flows_data['date'].max().normalize())
        self.clean_data = self.__clean_main_data()


    def __clean_main_data(self):
        ''' Cleans the dataframe obtained from the main collection for further processing.

        Returns:
            DataFrame: A cleaned DataFrame containing essential fields such as date,
            ticker, platform, and unit of account data.
        '''

        data = self.main_collection.document_query({})
        data['date_only'] = data['date'].dt.normalize()
        clean_df = data[['date', 'date_only', self.unit_of_account_col_name, self.ticker_col_name, 'asset_class', 'platform']]
        return clean_df


    def balance_by_platform_and_asset(self):
        ''' Calculates the balance of assets grouped by platform and asset class.

        This method organizes data by platform and ticker, computes cumulative balances,
        and creates a pivot table of balances over a specified date range.

        Returns:
            DataFrame: A DataFrame with the daily balances grouped by platform and asset class.
            The index represents the date range, and columns represent accounts (platform + ticker).
        '''

        balance_df = self.clean_data.copy(deep=True)
        balance_df['account'] = balance_df['platform'] + ' - ' + balance_df[self.ticker_col_name]
        balance_df.sort_values(by=['account', 'date'], inplace=True)
        balance_df['daily_balance'] = balance_df.groupby(['account'])[self.unit_of_account_col_name].cumsum()
        balances_units = balance_df.pivot_table(index='date_only', columns='account', values='daily_balance', aggfunc='last').reindex(self._date_range).ffill()
        return balances_units.fillna(0)




z = CollectionService(main_collection_name='cryptos_ledger', unit_of_account_col_name='units', ticker_col_name='ticker')
z2 = z.balance_by_platform_and_asset()
z3 = z.clean_data
z3 = z3.loc[(z3['platform']=='Kraken') & (z3['ticker']=='ETH-USD')]
z3['units'].sum()
