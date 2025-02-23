''' Functional file related to MongoDB database management
(Connection to the db, writing and querying of the data) '''

import pandas as pd
from pymongo import MongoClient, errors




class DataBaseConnect:
    ''' Super Class meant to handle database connection / creation.

    Attributes
    ----------
    database_name : str
        MongoDB database to connect to.
    client_address : str, optional
        MongoDB server address to connect to. The default is 'mongodb://localhost:27017/' (to run on a local MongoDB server).

    '''

    def __init__(self, database_name, client_address='mongodb://localhost:27017/'):
        self.client = MongoClient(client_address)
        self.database_list = self.client.list_database_names()
        self.database = self.__database_connect(database_name)


    def __database_connect(self, name):
        ''' Initiates the connection to the MongoDB database, if the db does not exists, prompt the user for creation confirmation.

        Parameters
        ----------
        name : str
            Name of the database in MongoDB.

        Returns
        -------
        synchronous.database.Database
            The MongoDB database ready to be used.

        '''

        if name not in self.database_list:
            creation_confirmation = input('The database does not exist, do you want to create it (True / False): ')
            self.creation_user_choice(creation_confirmation)
        return self.client[name]


    def creation_user_choice(self, user_choice):
        ''' Based on user_choice creates or not the MongoDB instance.

        If the user prompt Y, the method will continue to run, else it will avoid creating the instance.

        Parameters
        ----------
        user_choice : boolean
            True / False based on user choice to create a new instance or not.

        '''

        if user_choice == 'True':
            return None
        raise SystemExit('Provided name does not exist')



class CollectionConnect(DataBaseConnect):
    ''' Class meant to handle collection connection / creation based on inherited db connection

    Attributes
    ----------
    database_name : str
        MongoDB database to connect to.
    client_address : str, optional
        MongoDB server address to connecting to. The default is 'mongodb://localhost:27017/'.

    '''

    def __init__(self, collection_name, database_name, client_address='mongodb://localhost:27017/'):
        super().__init__(database_name=database_name, client_address=client_address)
        self.collection_list = self.database.list_collection_names()
        self.collection = self.__collection_connect(collection_name)


    def __collection_connect(self, name):
        ''' Initiates the connection to the MongoDB collection, if the collection does not exists, prompt the user for creation confirmation.

        Parameters
        ----------
        name : str
            Name of the database in MongoDB.

        Returns
        -------
        synchronous.collection.Collection
            The MongoDB collection ready to be used.

        '''

        if name not in self.collection_list:
            creation_confirmation = input('The collection does not exist in this database, do you want to create it (True / False): ')
            self.creation_user_choice(creation_confirmation)
        return self.database[name]


    def collection_writer(self, data, id_column_name=False):
        ''' Includes the element of data into the MongoDB collection.

        Parameters
        ----------
        data : pandas.DataFrame
            Data to be included in the MongoDB collection.
        id_column_name : str
            Name of the column that should be considered as MongoDB as the _id (unique identifier) of each document.

        '''

        for _, row in data.iterrows():
            mongodb_fields = row.to_dict()
            if id_column_name:
                mongodb_fields['_id'] = mongodb_fields[id_column_name]
            try:
                self.collection.insert_one(mongodb_fields)
            except errors.DuplicateKeyError:
                self.collection.update_one({'_id': mongodb_fields['_id']}, {'$set': mongodb_fields}, upsert=True)


    def document_query(self, query_dict):
        ''' Retrieves document(s) from the collection based on the query dict match

        Parameters
        ----------
        query_dict : dict
            Dictionnary with the filters that should be applied for the query (key / value in the dict same as in the document).
            ex: {"age": {"$gt": 25}, "city": "New York"}

        Returns
        -------
        dict
            Query output (elements of the collection for which the filters match.

        '''

        if query_dict:
            query_output = self.collection.find(query_dict)
        else:
            query_output = self.collection.find() # returns the full collection if no filter is specified
        return pd.DataFrame(query_output)





if __name__ == '__main__':
    test_collection = CollectionConnect(database_name='capital_vault', collection_name='cash_flows')
    test_filtered_output = test_collection.document_query({})
