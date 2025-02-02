import pandas as pd

from Longterm_investment.services.collections._collections_services_util import CollectionService



class CashFlowService(CollectionService):
    ''' A class to process and analyze cash flow data.

    Inherits from `CollectionService` and extends its functionality to provide computations for cash flow balances
    in different formats, including balances by platform, asset, or in aggregated form. It also allows for output in both
    the native currency units and CHF (Swiss Francs).
    '''

    def __init__(self):
        super().__init__(main_collection_name='cash_flows', unit_of_account_col_name='amount', ticker_col_name='currency')


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

        ccy = [account.split(' - ')[1] for account in balance_units.columns]
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






if __name__ == '__main__':
    cash_object = CashFlowService()
    # z = cash_object.balance_by_platform_and_asset(units_output=False)
    # filtered_columns = [col if 'Revolut' in col else '' for col in z.columns]
    # filtered_columns = list(filter(lambda x: x != '', filtered_columns))
    # z1 = z[filtered_columns]

