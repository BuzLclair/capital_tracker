import pandas as pd

from Longterm_investment.services.collections._collections_services_util import CollectionService




class MoneyMarketService(CollectionService):
    ''' A class to process and analyze fixed income data.

    Inherits from `CollectionService` and extends its functionality to provide computations for cryptocurrency balances,
    including balances by platform, asset, or in aggregated form. It also allows for output in both cryptocurrency
    units and CHF (Swiss Francs), using historical price and exchange rate data.
    '''

    def __init__(self):
        super().__init__(main_collection_name='fixed_income_ledger', unit_of_account_col_name='amount', ticker_col_name='isin')
        self.fx_dict = dict(self.main_collection.document_query({})[['isin', 'currency']].drop_duplicates().values)


    def balance_by_platform_and_asset(self, units_output=False):
        ''' Calculates cash flow balances grouped by platform and asset (optionally converts the balances to CHF using exchange rates).

        Args:
            units_output (bool, optional): If True, returns balances in native
            currency units. If False, converts the balances to CHF using the
            provided forex data. Defaults to False.

        Returns:
            DataFrame: A DataFrame containing daily balances grouped by platform
            and asset. The output can be either in native currency units or CHF.
        '''

        balance_units = super().balance_by_platform_and_asset()
        if units_output:
            return balance_units

        ccy_prep = [account.split(' - ')[1] for account in balance_units.columns]
        ccy = [self.fx_dict[isin] for isin in ccy_prep]
        fx_matrix = pd.DataFrame(columns=ccy, index=self._date_range, data=self.fx_data)
        balances_chf = balance_units * fx_matrix.values
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
        prices_matrix = pd.DataFrame(columns=tickers, index=self._date_range, data=1).fillna(0)
        balances_local_ccy = balance_units * prices_matrix.values

        tickers_ccy_df = self.main_collection.document_query({})[['isin', 'currency']].drop_duplicates()
        ticker_to_currency = tickers_ccy_df.set_index('isin')['currency'].to_dict()
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
        ''' Calculates daily fixed income balances grouped by asset (ticker) and optionally
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
        ''' Calculates daily balances grouped by platform.

        Returns:
            DataFrame: A DataFrame containing daily balances grouped by platform.
        '''

        account_balances = self.balance_by_platform_and_asset().copy(deep=True)
        account_balances.columns = [col.split(' - ')[0] for col in account_balances.columns]
        account_balances = account_balances.T.groupby(account_balances.columns).sum().T
        return account_balances


    def balance_aggregated(self):
        ''' Calculates the aggregated daily balance across all platforms and assets.

        Returns:
            Series: A pandas Series containing the aggregated daily balance.
        '''

        accounts_balance = self.balance_by_platform()
        return accounts_balance.sum(axis=1)
