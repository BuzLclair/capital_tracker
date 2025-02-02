import pandas as pd

from Longterm_investment.data.market_data.market_data_extract import SecuritiesData
from Longterm_investment.services.collections._collections_services_util import CollectionService




class SecuritiesService(CollectionService):
    ''' A class to process and analyze securities data.

    Inherits from `CollectionService` and extends its functionality to provide computations for securities balances,
    including balances by platform, asset, or in aggregated form. It also allows for output in both securities
    units and CHF (Swiss Francs), using historical price and exchange rate data.
    '''

    def __init__(self):
        super().__init__(main_collection_name='securities_ledger', unit_of_account_col_name='units', ticker_col_name='ticker')
        self.prices_data = SecuritiesData().clean_data()



    def balance_by_platform_and_asset(self, units_output=False):
        ''' Calculates securities balances grouped by platform and asset. (optionally
        converts the balances to CHF equivalent using historical price and exchange rate data).

        Args:
            units_output (bool, optional): If True, returns balances in cryptocurrency
            units. If False, converts the balances to CHF using historical price and
            exchange rate data. Defaults to False.

        Returns:
            DataFrame: A DataFrame containing daily balances grouped by platform
            and asset. The output can be either in securities units or CHF.
        '''

        balance_units = super().balance_by_platform_and_asset()
        if units_output:
            return balance_units

        tickers = [account.split(' - ')[1] for account in balance_units.columns]
        prices_matrix = pd.DataFrame(columns=tickers, index=self._date_range, data=self.prices_data).fillna(0)
        balances_local_ccy = balance_units * prices_matrix.values

        tickers_ccy_df = self.main_collection.document_query({})[['ticker', 'quote_currency']].drop_duplicates()
        ticker_to_currency = tickers_ccy_df.set_index('ticker')['quote_currency'].to_dict()
        currencies_list = [ticker_to_currency.get(ticker, 'Unknown') for ticker in tickers]
        fx_matrix = pd.DataFrame(columns=currencies_list, index=self._date_range, data=self.fx_data)
        balances_chf = balances_local_ccy * fx_matrix.values
        return balances_chf.ffill().round(2)


    def balance_by_currency(self, units_output=False):
        ''' Calculates daily balances grouped by currency and optionally outputs balances in native currency units or converts to CHF.

        Args:
            units_output (bool, optional): If True, returns balances in native
            currency units. If False, converts the balances to CHF. Defaults to False.

        Returns:
            DataFrame: A DataFrame containing daily balances grouped by currency.
        '''

        balance_units = super().balance_by_platform_and_asset()

        tickers = [account.split(' - ')[1] for account in balance_units.columns]
        prices_matrix = pd.DataFrame(columns=tickers, index=self._date_range, data=self.prices_data).fillna(0)
        balances_local_ccy = balance_units * prices_matrix.values

        tickers_ccy_df = self.main_collection.document_query({})[['ticker', 'quote_currency']].drop_duplicates()
        ticker_to_currency = tickers_ccy_df.set_index('ticker')['quote_currency'].to_dict()
        currencies_list = [ticker_to_currency.get(ticker, 'Unknown') for ticker in tickers]
        balances_local_ccy.columns = currencies_list
        balances_local_ccy = balances_local_ccy.T.groupby(balances_local_ccy.T.index).sum().T
        balances_local_ccy.columns = [ccy.replace('GBX', 'GBP') for ccy in balances_local_ccy.columns]
        if units_output:
            return balances_local_ccy

        fx_matrix = pd.DataFrame(columns=balances_local_ccy.columns, index=self._date_range, data=self.fx_data)
        balances_chf = balances_local_ccy * fx_matrix.values
        return balances_chf.fillna(0).round(2)


    def balance_by_asset(self, units_output=False):
        ''' Calculates daily cryptocurrency balances grouped by asset (ticker) and optionally
        outputs balances in cryptocurrency units or converts to CHF.

        Args:
            units_output (bool, optional): If True, returns balances in cryptocurrency
            units. If False, converts the balances to CHF. Defaults to False.

        Returns:
            DataFrame: A DataFrame containing daily balances grouped by ticker.
        '''

        if units_output:
            balance_df = self.balance_by_platform_and_asset(units_output=True).copy(deep=True)
        else:
            balance_df = self.balance_by_platform_and_asset().copy(deep=True)
        balance_df.columns = [col.split(' - ')[1] for col in balance_df.columns]
        return balance_df.T.groupby(balance_df.columns).sum().T


    def balance_by_platform(self):
        ''' Calculates daily cryptocurrency balances grouped by platform.

        Returns:
            DataFrame: A DataFrame containing daily balances grouped by platform.
        '''

        account_balances = self.balance_by_platform_and_asset().copy(deep=True)
        account_balances.columns = [col.split(' - ')[0] for col in account_balances.columns]
        account_balances = account_balances.T.groupby(account_balances.columns).sum().T
        return account_balances


    def balance_aggregated(self):
        ''' Calculates the aggregated daily cryptocurrency balance across all platforms and assets.

        Returns:
            Series: A pandas Series containing the aggregated daily balance.
        '''

        accounts_balance = self.balance_by_platform()
        return accounts_balance.sum(axis=1)





if __name__ == '__main__':
    secu_object = SecuritiesService()
    # z = secu_object.balance_by_platform_and_asset(units_output=False)
    # filtered_columns = [col if 'Interactive' in col else '' for col in z.columns]
    # filtered_columns = list(filter(lambda x: x != '', filtered_columns))
    # z1 = z[filtered_columns]
