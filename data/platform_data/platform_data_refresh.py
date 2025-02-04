import importlib
import pandas as pd

from Longterm_investment.data.database_studio import CollectionConnect


PLATFORMS = ['bcge', 'etoro', 'ibkr', 'kraken', 'revolut']
PLATFORMS_MODULES = {}

for platform in PLATFORMS:
    PLATFORMS_MODULES[platform] = importlib.import_module(f'Longterm_investment.data.platform_data.{platform}.{platform}_data_extract')





def generate_id_col(time_col, *args):
    ''' Generate a unique ID for each row by combining a timestamp and additional column values.

    Parameters
    ----------
    time_col : datetime
        A datetime object representing the timestamp for the row.
    *args : tuple
        Additional arguments (column values) to include in the ID.

    Returns
    -------
    list
        A list of unique identifiers in the format "{timestamp} - {arg1} - {arg2} - ...".
    '''

    timestamp = int(time_col.timestamp())
    return f"{timestamp} - " + ' - '.join(map(str, args))



def balance_calc(df, amount_col='amount', ccy_col='currency'):
    ''' Calculate a cumulative balance grouped by categories and add a unique identifier column (_id, that will be used to write the data into MongoDB).

    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame containing transaction data.
    amount_col : str, optional
        The name of the column representing transaction amounts (default is 'amount').
    ccy_col : str, optional
        The name of the column representing currencies (default is 'currency').

    Returns
    -------
    pandas.DataFrame
        A DataFrame with two additional columns:
        - 'balance_by_cat': The cumulative sum of the amount column grouped by
          [currency, platform, type], sorted by date and amount.
        - '_id': A unique identifier generated for each row.
    '''

    df = df.sort_values(by=['date', amount_col], ascending=[True, True]).copy()
    df_temp = df.copy()
    df_temp['amount_abs'] = abs(df_temp[amount_col])
    df_temp['balance_by_cat'] = df_temp.groupby([ccy_col, 'platform', 'type'])['amount_abs'].cumsum()
    df['_id'] = df_temp[['date', 'type', amount_col, ccy_col, 'platform', 'balance_by_cat']].apply(lambda row: generate_id_col(row['date'], *row[1:]), axis=1)
    return df






class CapitalVaultDataFeed:
    '''
    A class to manage data feeds and handle interactions with various data sources and collections.

    This class handles the extraction of data from various platforms, cleans and processes the data,
    and writes it to the appropriate MongoDB collections.
    '''

    def __init__(self):
        self.platforms = PLATFORMS
        self.collection_cash_flows = CollectionConnect(database_name='capital_vault', collection_name='cash_flows')
        self.collection_securities_ledger = CollectionConnect(database_name='capital_vault', collection_name='securities_ledger')
        self.collection_cryptos = CollectionConnect(database_name='capital_vault', collection_name='cryptos_ledger')
        self.collection_fixed_income = CollectionConnect(database_name='capital_vault', collection_name='fixed_income_ledger')


    def get_collections(self, start_date=None):
        '''
        Retrieves and processes data from various platforms.

        Loops over the each platform predefined data extract method by calling the `main()`
        method to extract the data of each platform. It then returns the processed data as a list of sub_collections.

        Returns
        -------
        collection_list : list
            A list of dictionaries, where each dictionary contains the data and metadata for a specific collection.
        '''

        collection_list = []
        for platform in self.platforms:
            collection = PLATFORMS_MODULES[platform].main()

            if start_date:
                for idx in range(len(collection)):
                    df = collection[idx]['DataFrame']
                    df['date'] = pd.to_datetime(df['date'], utc=True)
                    collection[idx]['DataFrame'] = df.loc[df['date'] >= start_date]

            collection = list(filter(lambda x: x['DataFrame'].empty==False, collection))
            collection_list += collection
        return collection_list


    def write_collection(self, collection):
        ''' Cleans the data and writes it to the appropriate MongoDB collection.

        Parameters
        ----------
        collection : dict
            A dictionary containing the data frame, amount column name, currency column name,
            and the target collection name to which the cleaned data will be written.
        '''

        clean_df = balance_calc(collection['DataFrame'], collection['amount_col'], collection['ccy_col'])
        collection = getattr(self, collection['destination_collection'], None)
        collection.collection_writer(clean_df, id_column_name='_id')


    def data_feed(self, update=False):
        ''' Orchestrates the entire data feed process.

        Parameters
        ----------
        update : bool, optional
            If True, performs an incremental update by processing data starting from
            the first day of the current year. If False, processes all available data
            (default is False).

        '''

        start_date = None
        if update:
            start_date = pd.to_datetime(f'{pd.Timestamp.now().year}-01-01', utc=True)
        collection_list = self.get_collections(start_date)
        for sub_collection in collection_list:
            self.write_collection(sub_collection)





if __name__ == '__main__':
    CapitalVaultDataFeed().data_feed(update=False)
