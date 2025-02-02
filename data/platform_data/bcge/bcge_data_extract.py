import os
import re
import pandas as pd
import numpy as np

from Longterm_investment.data.platform_data.bcge.bcge_data_validation_test import test_bcge_data_extract
from Longterm_investment.data.platform_data._data_extract_util import collection_config


RAW_DATA_PATH = os.environ.get("capital_tracker_raw_data")
EXCEL_EXTRACT_PATH = f'{RAW_DATA_PATH}/bcge/bcge_data_extraction.xlsx'



def loading_and_preclean_data():
    df = pd.read_excel(EXCEL_EXTRACT_PATH)

    df['Column3'] = df['Column1'].fillna('') + ' ' + df['Column2'].fillna('') + ' ' + df['Column3'].fillna('')
    df['Column3'] = df['Column3'].replace('  ', np.nan)
    df.drop(columns=['Column1', 'Column2', 'Column13'], inplace=True)

    mask = df.loc[:, 'Column4':'Column12'].isna().all(axis=1)
    previous_index = None
    merged_values = []

    for idx in df.index:
        if mask[idx]:
            value = df.at[idx, 'Column3']
            if pd.notna(value):
                merged_values.append(str(value))
        else:
            if merged_values and previous_index is not None:
                df.at[previous_index, 'Column3'] = f"{df.at[previous_index, 'Column3']} {' '.join(merged_values)}".strip()
                merged_values = []
            previous_index = idx

    if merged_values and previous_index is not None:
        df.at[previous_index, 'Column3'] = f"{df.at[previous_index, 'Column3']} {' '.join(merged_values)}".strip()

    df = df[~mask].reset_index(drop=True)
    return df


def filtering_df(df, process_dict):
    mask = df.loc[:, process_dict['mask_na']].isna().all(axis=1) & df.loc[:, process_dict['mask_notna']].notna().all(axis=1)
    shifted_col = process_dict['shifted_col']
    df.loc[mask, shifted_col] = df.loc[mask, shifted_col].shift(periods=process_dict['shifted_periods'], axis=1)
    return df


def process_dataframe(df):
    basic_shifted_col = df.loc[:, 'Column4':'Column12'].columns
    processing_list1 = [
        {'mask_notna': ['Column3', 'Column8'], 'mask_na': ['Column4', 'Column5', 'Column6', 'Column7'], 'shifted_col': basic_shifted_col, 'shifted_periods': -4},
        {'mask_notna': ['Column3', 'Column9'], 'mask_na': ['Column4', 'Column5', 'Column6', 'Column7', 'Column8'], 'shifted_col': basic_shifted_col, 'shifted_periods': -5},
        {'mask_notna': ['Column3'], 'mask_na': ['Column4', 'Column5', 'Column6'], 'shifted_col': basic_shifted_col, 'shifted_periods': -3},
        {'mask_notna': ['Column3'], 'mask_na': ['Column4', 'Column5'], 'shifted_col': basic_shifted_col, 'shifted_periods': -2},
        {'mask_notna': ['Column3', 'Column5'], 'mask_na': ['Column4'], 'shifted_col': basic_shifted_col, 'shifted_periods': -1}]

    processing_list2 = [
        {'mask_notna': ['Column3', 'Column4', 'Column5'], 'mask_na': ['Column6', 'Column7'], 'shifted_col': df.loc[:, 'Column7':'Column12'].columns, 'shifted_periods': -1},
        {'mask_notna': ['Column4', 'Column6'], 'mask_na': ['Column3', 'Column5'], 'shifted_col': df.loc[:, 'Column5':'Column12'].columns, 'shifted_periods': -1},
        {'mask_notna': ['Column4', 'Column5'], 'mask_na': ['Column3'], 'shifted_col': df.columns, 'shifted_periods': -1},
        {'mask_notna': ['Column3', 'Column4', 'Column6', 'Column8'], 'mask_na': ['Column7'], 'shifted_col': df.loc[:, 'Column7':'Column12'].columns, 'shifted_periods': -1},
        {'mask_notna': ['Column3', 'Column4', 'Column7', 'Column8'], 'mask_na': ['Column5'], 'shifted_col': df.loc[:, 'Column6':'Column12'].columns, 'shifted_periods': -1},
        {'mask_notna': ['Column3', 'Column4'], 'mask_na': ['Column5', 'Column6'], 'shifted_col': df.loc[:, 'Column5':'Column12'].columns, 'shifted_periods': -1},]

    for process_dict in processing_list1:
        df = filtering_df(df, process_dict)

    df = df.loc[~df['Column3'].str.contains('Solde au', na=False)]
    df = df.loc[~df['Column3'].str.contains('Intérêt créditeur', na=False)]

    for process_dict in processing_list2:
        df = filtering_df(df, process_dict)

    mask12 = (df.loc[:, ['Column3', 'Column4', 'Column5']].notna().all(axis=1)) & (df['Column5'].astype(str).str.count(r'\.') == 2)
    df.loc[mask12, 'Column3'] = df.loc[mask12, 'Column3'] + ' ' + df.loc[mask12, 'Column4']
    df.loc[mask12, basic_shifted_col] = df.loc[mask12, basic_shifted_col].shift(periods=-1, axis=1)
    return df


def extract_datetime(text):
    match = re.search(r"\b\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}\b", text)
    return match.group(0) if match else None


def cleaning_data(df):
    df = df[(df['Column4'].astype(str).str.count(r'\.') == 2) & (df['Column4'].str.len()==8)]

    df = df.drop(columns=['Column8', 'Column9', 'Column10', 'Column11', 'Column12'])
    df.columns = ['description', 'date', 'out', 'in', 'balance']

    df['date'] = pd.to_datetime(df['date'], format='%d.%m.%y')
    df[['out', 'in', 'balance']] = df[['out', 'in', 'balance']].fillna(0).astype(str).replace("'", "", regex=True).astype(float)
    df['out'] = -df['out']

    temp_date = df['description'].apply(extract_datetime)
    temp_date = pd.to_datetime(temp_date, format='%d.%m.%Y %H:%M')
    df['date'] = temp_date.fillna(df['date'])

    df['description'] = df['description'].str.lstrip()

    df[['accounting_date', 'description']] = df['description'].str.split(' ', n=1, expand=True)
    df['accounting_date'] = pd.to_datetime(df['accounting_date'], format='%d.%m.%y')
    return df




def cash_flow_prep(df):
    ''' Extract the cash flows positions from cleaned account statements and returns a cleaned df.

    Returns
    -------
    cash_flows : DataFrame
        Cleaned cash flows df.

    '''

    cash_flows = df.copy()[['description', 'accounting_date', 'out', 'in', 'balance']]
    cash_flows.rename(columns={'accounting_date':'date'}, inplace=True)
    cash_flows['amount'] = cash_flows['out'] + cash_flows['in']

    initial_row = cash_flows.loc[cash_flows['date'] == min(cash_flows['date'])]
    new_row = pd.DataFrame({'date': min(cash_flows['date']), 'amount': abs(initial_row['amount']) + initial_row['balance'],
               'in':0, 'out':0, 'balance':0, 'description': 'Initial account balance'})
    cash_flows = pd.concat([cash_flows, new_row], ignore_index=True)

    cash_flows.loc[:, 'platform'] = 'BCGE'
    cash_flows['currency'] = 'CHF'

    cash_flows.loc[cash_flows['amount'] > 0, 'type'] = 'Deposit'
    cash_flows.loc[(cash_flows['amount'] < 0) & (cash_flows['description'].str.contains('Achat')), 'type'] = 'Expense'
    cash_flows.loc[(cash_flows['amount'] < 0) & (~cash_flows['description'].str.contains('Achat')), 'type'] = 'Withdrawal'
    cash_flows = cash_flows.loc[:, ('date', 'type', 'amount', 'platform', 'currency', 'description')]
    cash_flows['asset_class'] = 'Cash'
    return cash_flows



def main():
    df = loading_and_preclean_data()
    df = process_dataframe(df)
    df = cleaning_data(df)
    test_bcge_data_extract(df)

    cash_flows = collection_config(dataframe=cash_flow_prep(df), collection_name='collection_cash_flows')
    dfs_list = [cash_flows]
    return dfs_list


