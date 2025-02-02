import pandas as pd
import yfinance as yf

from Longterm_investment.data.database_studio import CollectionConnect


def get_prices(ticks, start_date=None, end_date=None):
    prices = yf.download(ticks, start=start_date, end=end_date, interval='1d')['Adj Close']
    return prices.astype('float32').ffill()




class __MarketPrices:
    ''' A class to manage external market data from a MongoDB collection, ensuring data completeness and consistency.

    Attributes:
    -----------
    collection : CollectionConnect
        Connection to the MongoDB collection storing the source data.
    data : pandas.DataFrame
        The current source data fetched from the database.
    start_date : datetime
        The earliest date for which market data is needed.
    end_date : datetime
        The latest date for which market data is needed.
    needed_tickers : list
        A list of all required tickers based on the given source data.
    '''

    def __init__(self, collection_name, source_collection_lst, source_columns_names):
        self.collection = CollectionConnect(database_name='capital_vault', collection_name=collection_name)
        self.data = self.collection.document_query({})
        self.start_date, self.end_date, self.needed_tickers = self.__get_meta_data(source_collection_lst, source_columns_names)


    def __get_meta_data(self, collection_lst, columns_names_lst):
        '''
        Fetches metadata from cash flows and securities ledger collections to determine:
        - The range of dates required.
        - The list of unique currencies needed.
        '''

        collections = [CollectionConnect(database_name='capital_vault', collection_name=collection) for collection in collection_lst]
        meta_dfs = []
        for idx in range(len(collection_lst)):
            meta_df = collections[idx].document_query({})[columns_names_lst[idx]]
            meta_df.columns = ['date', 'ticker']
            meta_dfs.append(meta_df)

        combined_meta = pd.concat(meta_dfs)
        start_date =  combined_meta['date'].min()
        end_date = combined_meta['date'].max()
        unique_ccy = combined_meta['ticker'].unique().tolist()
        return start_date, end_date, unique_ccy




class ForexData(__MarketPrices):
    '''
    A class to manage Forex data from a MongoDB collection, ensuring data completeness and consistency.
    Uses MarketPrices as parent class.

    Methods:
    --------
    update_fx_data():
        Updates the FX matrix data by fetching missing data and writing it to the database.
    '''

    def __init__(self):
        super().__init__(collection_name='fx_matrix', source_collection_lst=['cash_flows', 'securities_ledger'], source_columns_names=
                         [['date', 'currency'], ['date', 'quote_currency']])
        self.needed_tickers = ['GBP' if ticker == 'GBX' else ticker for ticker in self.needed_tickers]


    def __add_missing_dates(self, dates_to_fetch):
        ''' Adds FX data for missing dates and updates the FX matrix collection.

        Parameters:
        -----------
        dates_to_fetch : pandas.DatetimeIndex
            A range of dates for which FX data is missing and needs to be fetched.
        '''

        if dates_to_fetch.empty==False:
            currencies = self.needed_tickers.copy()
            currencies.remove('CHF')
            currencies = [ccy + 'CHF=X' for ccy in currencies]

            fx_matrix = get_prices(currencies, start_date=min(dates_to_fetch))
            fx_matrix.reset_index(inplace=True)
            fx_matrix['CHFCHF'] = 1
            fx_matrix['_id'] = fx_matrix['Date']
            fx_matrix.rename(columns={'Date':'date'}, inplace=True)
            fx_matrix.columns = [column.split('=X')[0] for column in fx_matrix.columns]
            self.collection.collection_writer(fx_matrix, '_id')
            self.data = self.collection.document_query({})


    def __add_missing_currencies(self):
        ''' Adds FX data for missing currencies and updates the FX matrix collection. '''

        actual_ccy = self.data.columns.tolist()
        actual_ccy = [ccy.replace('CHF', '') for ccy in actual_ccy]
        actual_ccy.remove('_id')
        actual_ccy.remove('date')
        missing_ccy = list(filter(lambda x: x not in actual_ccy, self.needed_tickers))

        if missing_ccy != ['CHF']:
            missing_ccy.remove('CHF')
            missing_ccy = [ccy + 'CHF=X' for ccy in missing_ccy]
            missing_data = get_prices(missing_ccy, start_date=self.start_date)
            missing_data = missing_data.loc[missing_data.index.isin(self.data['date'])]

            missing_ccy = [ccy.split('=X')[0] for ccy in missing_ccy]
            complete_data = self.data.copy()
            complete_data[missing_ccy] = missing_data.values
            self.collection.collection_writer(complete_data, '_id')
            self.data = self.collection.document_query({})


    def update_fx_data(self):
        ''' Method to update the FX collection. '''

        start_date = (min(self.data['date']) if not self.data.empty else self.start_date).tz_localize('UTC')
        actual_dates_range = pd.date_range(start=start_date, end=self.end_date.tz_localize('UTC'))
        dates_to_fetch = actual_dates_range[actual_dates_range > max(self.data['date']).tz_localize('UTC')] if not self.data.empty else actual_dates_range

        self.__add_missing_dates(dates_to_fetch)
        self.__add_missing_currencies()
        print('\033[1;32mFX matrix query update:\033[37m\033[3m The data is complete.\033[0m')


    def clean_fx_data(self):
        ''' Method to return a clean, ready to use fx df. '''

        fx_matrix = self.data.copy().drop(columns=['_id']).set_index('date')
        fx_matrix.columns = [col[:3] for col in fx_matrix.columns]
        date_range = pd.date_range(start=self.start_date.normalize(), end=pd.to_datetime('today').normalize())
        return fx_matrix.reindex(date_range.normalize()).ffill()



class SecuritiesData(__MarketPrices):
    '''
    A class to manage Stocks & Cryptos data from a MongoDB collection, ensuring data completeness and consistency.
    Uses MarketPrices as parent class.

    Methods:
    --------
    update_market_data():
        Updates the securities data by fetching missing data and writing it to the database.
    '''

    def __init__(self):
        super().__init__(collection_name='market_prices', source_collection_lst=['securities_ledger', 'cryptos_ledger'], source_columns_names=
                         [['date', 'ticker'], ['date', 'ticker']])
        self.ticker_corr = pd.read_excel(r'C:/Users/const/Documents/Code/Python/PlutusForge/Longterm_investment/services/ticker_corr.xlsx')



    def __add_missing_dates(self, dates_to_fetch):
        ''' Adds FX data for missing dates and updates the FX matrix collection.

        Parameters:
        -----------
        dates_to_fetch : pandas.DatetimeIndex
            A range of dates for which FX data is missing and needs to be fetched.
        '''

        if dates_to_fetch.empty==False:
            tickers = self.needed_tickers.copy()

            prices_df = get_prices(tickers, start_date=min(dates_to_fetch))
            prices_df.reset_index(inplace=True)
            prices_df['_id'] = prices_df['Date']
            prices_df.rename(columns={'Date':'date'}, inplace=True)
            self.collection.collection_writer(prices_df, '_id')
            self.data = self.collection.document_query({})


    def __add_missing_tickers(self):
        ''' Adds FX data for missing currencies and updates the FX matrix collection. '''

        actual_tickers = self.data.columns.tolist()
        actual_tickers.remove('_id')
        actual_tickers.remove('date')
        missing_tickers = list(filter(lambda x: x not in actual_tickers, self.needed_tickers))
        missing_tickers_filtered = list(filter(lambda x: x not in ['ATVI', 'RADCQ', 'TUI.L', 'EVVAQ'], missing_tickers))

        if missing_tickers_filtered != []:
            missing_data = get_prices(missing_tickers_filtered, start_date=self.start_date)
            missing_data = missing_data.loc[missing_data.index.isin(self.data['date'])]
            missing_data = missing_data.reset_index()
            missing_data.rename(columns={'Date':'date'}, inplace=True)

            complete_data = self.data.copy()
            complete_data_merged = pd.merge(complete_data, missing_data, on='date', how='left')
            complete_data_merged[missing_tickers_filtered] = complete_data_merged[missing_tickers_filtered].ffill()
            self.collection.collection_writer(complete_data_merged, '_id')
            self.data = self.collection.document_query({})


    def update_market_data(self):
        ''' Method to update the market_prices collection. '''

        start_date = (min(self.data['date']) if not self.data.empty else self.start_date).tz_localize('UTC')
        actual_dates_range = pd.date_range(start=start_date, end=self.end_date.tz_localize('UTC'))
        dates_to_fetch = actual_dates_range[actual_dates_range > max(self.data['date']).tz_localize('UTC')] if not self.data.empty else actual_dates_range

        self.needed_tickers = [ticker.replace('.US', '') for ticker in self.needed_tickers]

        self.__add_missing_dates(dates_to_fetch)
        self.__add_missing_tickers()
        print('\033[1;32mmarket_prices query update:\033[37m\033[3m The data is complete.\033[0m')


    def clean_data(self):
        ''' Method to return a clean, ready to use df. '''

        prices_matrix = self.data.copy().drop(columns=['_id']).set_index('date')
        date_range = pd.date_range(start=self.start_date.normalize(), end=pd.to_datetime('today').normalize())
        return prices_matrix.reindex(date_range.normalize()).ffill()



# z = SecuritiesData()
# z1 = z.clean_data()
