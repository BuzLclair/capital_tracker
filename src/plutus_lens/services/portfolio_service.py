import pandas as pd

from src.plutus_lens.services.collections import cash_flows_service, cryptos_service, securities_service, money_market_service





class PortfolioService:
    ''' A class to compute and aggregate portfolio balances across various asset classes, platforms,
    and currencies, leveraging data from cash flows, cryptocurrencies, and securities.

    Attributes:
        cash_flows_object (CashFlowService): Instance of the CashFlowService for managing cash flow data.
        cryptos_object (CryptoService): Instance of the CryptoService for managing cryptocurrency data.
        securities_object (SecuritiesService): Instance of the SecuritiesService for managing securities data.

    Methods:
        balance_by_asset_class():
            Computes the aggregated portfolio balance by asset class (cash flows, cryptos, and securities) in CHF.

        balance_by_platform():
            Computes the aggregated portfolio balance grouped by platforms across all asset classes.

        balance_by_currency():
            Computes the aggregated portfolio balance grouped by currency across cash flows and securities only.

        balance_total():
            Computes the total portfolio balance by summing up all platform-level balances.
    '''

    def __init__(self):
        self.cash_flows_object = cash_flows_service.CashFlowService()
        self.cryptos_object = cryptos_service.CryptoService()
        self.securities_object = securities_service.SecuritiesService()
        self.fixed_income_object = money_market_service.MoneyMarketService()


    def balance_by_asset_class(self):
        ''' Computes the aggregated portfolio balance by asset class (cash flows, cryptos, and securities) in CHF.

        Returns:
            pd.DataFrame: A DataFrame with the total balances for each asset class, where columns represent asset classes
                          and rows represent dates.
        '''

        cash_flows_total_balance_chf = self.cash_flows_object.balance_aggregated()
        cryptos_total_balance_chf = self.cryptos_object.balance_aggregated()
        securities_total_balance_chf = self.securities_object.balance_aggregated()
        fixed_income_total_balance_chf = self.fixed_income_object.balance_aggregated()

        balance_df = pd.DataFrame({'cash_flows':cash_flows_total_balance_chf, 'cryptos':cryptos_total_balance_chf, 'securities':securities_total_balance_chf,
                                   'fixed_income': fixed_income_total_balance_chf})
        return balance_df


    def balance_by_platform(self):
        ''' Computes the aggregated portfolio balance grouped by platforms across all asset classes.

        Returns:
            pd.DataFrame: A DataFrame with platform-level balances, where columns represent platforms and rows represent dates.
        '''

        cash_flows_platform_balance_chf = self.cash_flows_object.balance_by_platform()
        cryptos_platform_balance_chf = self.cryptos_object.balance_by_platform()
        securities_platform_balance_chf = self.securities_object.balance_by_platform()
        fixed_income_total_balance_chf = self.fixed_income_object.balance_by_platform()

        balance_df = pd.concat([cash_flows_platform_balance_chf, cryptos_platform_balance_chf, securities_platform_balance_chf,
                                fixed_income_total_balance_chf]).groupby(level=0).sum()
        return balance_df


    def balance_by_currency(self):
        ''' Computes the aggregated portfolio balance grouped by currency across cash flows and securities.
        Cryptocurrency balances are excluded from currency grouping since they are considered independent of currencies.

        Returns:
            pd.DataFrame: A DataFrame with currency-level balances, where columns represent currencies and rows represent dates.
        '''

        cash_flows_currency_balance_chf = self.cash_flows_object.balance_by_currency()
        securities_currency_balance_chf = self.securities_object.balance_by_currency()
        fixed_income_total_balance_chf = self.fixed_income_object.balance_by_currency()

        balance_df = pd.concat([cash_flows_currency_balance_chf, securities_currency_balance_chf, fixed_income_total_balance_chf]).groupby(level=0).sum()
        return balance_df


    def balance_total(self):
        ''' Computes the total portfolio balance by summing up all platform-level balances across all asset classes.

        Returns:
            pd.Series: A Series representing the total portfolio balance for each date.
        '''

        balance_by_platform = self.balance_by_platform()
        balance_df = balance_by_platform.sum(axis=1)
        return balance_df




z = PortfolioService()
z1 = z.balance_total()
