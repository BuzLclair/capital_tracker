import os
import re
import pandas as pd
import numpy as np

from .bcge_data_validation_test import test_bcge_data_extract
# from bcge_data_validation_test import test_bcge_data_extract
from src.plutus_lens.data import collection_config


RAW_DATA_PATH = os.environ.get("capital_tracker_raw_data")
EXCEL_EXTRACT_PATH = f'{RAW_DATA_PATH}/bcge/bcge_data_extraction.xlsx'



def loading_and_preclean_data():
    df = pd.read_excel(EXCEL_EXTRACT_PATH)

    df = df.loc[~(df.iloc[:,:7].isna().all(axis=1))]
    df['Column3'] = df['Column1'].fillna('') + ' ' + df['Column2'].fillna('') + ' ' + df['Column3'].fillna('') + df['Column4'].fillna('')
    df['Column3'] = df['Column3'].str.lstrip()
    df.drop(columns=['Column1', 'Column2', 'Column4', 'Column13'], inplace=True)

    for txt in ['CP 2251 - 1211 Genève 2', 'A défaut d\'une réclamation écrite reçue par la banque', 'de comptes sont tenus pour approuvés.', '58 211 21 00', '0000OOKUP,fodLkup', 'Solde au']:
        df.loc[((df['Column3'].astype(str).str.contains(txt)))] = ''
    df.loc[(df['Column3'] == '')] = ''

    df = df.loc[df['Column3'] == df['Column3']]
    temp_index = ((df['Column3'].str[:6].str.count(r'\.')==2) & (df['Column3'].str[:6].str.count(' ')==0)) * df.index
    temp_index = temp_index.replace(0, np.nan).ffill(limit=2)

    df['test'] = temp_index
    df = df.loc[df['test'] == df['test']]

    df_cleaned = df.fillna('').groupby('test').transform(lambda x: ' '.join(x.astype(str))).drop_duplicates()
    df_cleaned = df_cleaned.map(lambda x: re.sub(r'\s+', ' ', x).strip() if isinstance(x, str) else x)
    return df_cleaned



def clean_list(lst):
    date_pattern = re.compile(r'\b\d{2}\.\d{2}\.\d{2}\b')
    cleaned_list, found_date, prev_blank = [lst[0]], False, False

    for val in lst[1:]:
        if not found_date:
            if date_pattern.match(val):
                found_date = True
                cleaned_list.append(val)
        else:
            if val.strip():
                cleaned_list.append(val)
                prev_blank = False
            elif not prev_blank:
                cleaned_list.append(val)
                prev_blank = True
    return cleaned_list


def extract_datetime(text):
    match = re.search(r"\b\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}\b", text)
    return match.group(0) if match else None


def clean_dataframe(df):
    cleaned_rows = []
    for element in df.values.tolist():
        cleaned_rows.append(clean_list(element))
    df_cleaned = pd.DataFrame(cleaned_rows)
    df_cleaned = df_cleaned.iloc[:, :5]

    df_cleaned.columns = ['description', 'date', 'out', 'in', 'balance']
    df_cleaned = df_cleaned.loc[~df_cleaned[['date', 'out', 'in', 'balance']].isna().all(axis=1)]
    df_cleaned['date'] = pd.to_datetime(df_cleaned['date'], format='%d.%m.%y')
    df_cleaned[['out', 'in', 'balance']] = df_cleaned[['out', 'in', 'balance']].replace('', np.nan)
    df_cleaned[['out', 'in', 'balance']] = df_cleaned[['out', 'in', 'balance']].fillna(0).astype(str).replace("'", "", regex=True).astype(float)
    df_cleaned['out'] = -df_cleaned['out']

    temp_date = df_cleaned['description'].apply(extract_datetime)
    temp_date = pd.to_datetime(temp_date, format='%d.%m.%Y %H:%M')
    df_cleaned['date'] = temp_date.fillna(df_cleaned['date'])

    df_cleaned['description'] = df_cleaned['description'].str.lstrip()

    df_cleaned[['accounting_date', 'description']] = df_cleaned['description'].str.split(' ', n=1, expand=True)
    df_cleaned['accounting_date'] = pd.to_datetime(df_cleaned['accounting_date'], format='%d.%m.%y')
    return df_cleaned






def clean_cash_flows(df):
    ''' Clean the text to get the proper french accents (equivalent to UTF-8 decode result) '''

    replacements = [("Ã©", "é"),("Ã¨", "è"),("Ã ", "à"),("Ã§", "ç"),("Ãª", "ê"),("Ã¯", "ï"),("Ã´", "ô"),("Ã¼", "ü"),("Ãœ", "Ü"),("Ã†", "Æ"),("Ã“", "Ó"),("Ã", "à"),("Œ", "œ"),("Â", ""),("\n",""),("Â°","o")]
    for old, new in replacements:
        df['description'] = df['description'].str.replace(old, new, regex=False)
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

    cash_flows.loc[cash_flows['amount'] >= 0, 'type'] = 'Inflow'
    cash_flows.loc[cash_flows['amount'] < 0, 'type'] = 'Outflow'

    cash_flows.loc[cash_flows['description'].str.contains('Constantin Bosc') | cash_flows['description'].str.contains('Constantin Jean-Pierre Francois'), ('type', 'subtype')] = ['Transfer', 'Variable']
    cash_flows.loc[cash_flows['description'].str.contains('Ordre permanent') | cash_flows['description'].str.contains('Avenue de France 90'), 'subtype'] = 'Fixed'
    cash_flows.loc[cash_flows['description'].str.contains('EM Exchange Market') | cash_flows['description'].str.contains('WIR Bank Auberg 1') |
                   cash_flows['description'].str.contains('Revolut Bank UAB'), ('type', 'subtype')] = ['Transfer', 'Variable']

    cash_flows.loc[(cash_flows['type']=='Outflow') & ((cash_flows['description'].str.contains('Sanitas')) | (cash_flows['description'].str.contains('Helsana'))), 'subtype'] = 'Fixed'
    cash_flows.loc[(cash_flows['type']=='Inflow') & ((cash_flows['description'].str.contains(' Ernst & Young AG')) | (cash_flows['description'].str.contains(' Ernst . Young AG')) | (cash_flows['description'].str.contains('CH580024024087252802T'))), 'subtype'] = 'Fixed'
    cash_flows.loc[cash_flows['subtype'] != cash_flows['subtype'], 'subtype'] = 'Variable'
    cash_flows = cash_flows.loc[:, ('date', 'type', 'subtype', 'amount', 'platform', 'currency', 'description')]
    cash_flows['asset_class'] = 'Cash'
    cash_flows = clean_cash_flows(cash_flows)
    return cash_flows






def main():
    df = loading_and_preclean_data()
    df = clean_dataframe(df)
    test_bcge_data_extract(df)

    cash_flows = collection_config(dataframe=cash_flow_prep(df), collection_name='collection_cash_flows')
    dfs_list = [cash_flows]
    return dfs_list





if __name__ == '__main__':
    test = main()
