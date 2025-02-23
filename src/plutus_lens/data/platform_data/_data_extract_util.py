

def collection_config(dataframe, collection_name, amount_col='amount', ccy_col='currency'):
    return {
        'DataFrame': dataframe,
        'destination_collection': collection_name,
        'amount_col': amount_col,
        'ccy_col': ccy_col
    }
