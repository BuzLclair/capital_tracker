import pandas as pd

from Longterm_investment.data.market_data.market_data_extract import SecuritiesData
from Longterm_investment.services.collections._collections_services_util import CollectionService




class CryptoService(CollectionService):
    ''' A class to process and analyze cryptocurrency data.

    Inherits from `CollectionService` and extends its functionality to provide computations for cryptocurrency balances,
    including balances by platform, asset, or in aggregated form. It also allows for output in both cryptocurrency
    units and CHF (Swiss Francs), using historical price and exchange rate data.
    '''

    def __init__(self):
        super().__init__(main_collection_name='cryptos_ledger', unit_of_account_col_name='units', ticker_col_name='ticker')
        self.prices_data = SecuritiesData().clean_data()


    def balance_by_platform_and_asset(self, units_output=False):
        ''' Calculates cryptocurrency balances grouped by platform and asset. (optionally
        converts the balances to CHF equivalent using historical price and exchange rate data).

        Args:
            units_output (bool, optional): If True, returns balances in cryptocurrency
            units. If False, converts the balances to CHF using historical price and
            exchange rate data. Defaults to False.

        Returns:
            DataFrame: A DataFrame containing daily balances grouped by platform
            and asset. The output can be either in cryptocurrency units or CHF.
        '''

        balance_units = super().balance_by_platform_and_asset()
        if units_output:
            return balance_units

        tickers = [account.split(' - ')[1] for account in balance_units.columns]
        prices_matrix = pd.DataFrame(columns=tickers, index=self._date_range, data=self.prices_data).fillna(0)
        balances_usd = balance_units * prices_matrix.values

        ccy = ['USD' for col in balances_usd.columns]
        fx_matrix = pd.DataFrame(columns=ccy, index=self._date_range, data=self.fx_data)
        balances_chf = balances_usd * fx_matrix.values
        return balances_chf.ffill().round(2)


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
    crypto_object = CryptoService()
    z = crypto_object.balance_by_platform_and_asset(units_output=False)
    filtered_columns = [col if 'Kraken' in col else '' for col in z.columns]
    filtered_columns = list(filter(lambda x: x != '', filtered_columns))
    z1 = z[filtered_columns]

