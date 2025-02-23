''' Check if in the BCGE cleaned data is correct (i.e if the sum of initial cash flows + outflows + inflows equal to the final cash flows '''


def test_bcge_data_extract(df):
    """
    Validates the balance of the DataFrame based on the specific logic.
    Returns True if the test passes, False otherwise.
    """
    # Calculate the validation result
    result = round(df['balance'].iloc[0] - df['out'].iloc[0] + df['out'].sum() + df['in'].sum() - df['balance'].iloc[-1], 2)
    if result == 0:
        return None
    else:
        print('\033[1;31mERROR - BCGE data reconciliation is incorrect\033[0m')



if __name__ == '__main__':
    test_bcge_data_extract()
