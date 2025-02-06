import pandas as pd

from Longterm_investment.services.collections import cash_flows_service



class DataPackage:

    def __init__(self):
        self.cash_flows_object = cash_flows_service.CashFlowService()
        self.data = self.cash_flows_object.main_collection.document_query({})


    def cleaned_data(self):
        data = self.data[['platform', 'type', 'date', 'currency', 'amount', 'description']].copy()
        data = data.sort_values(by='date', ascending=False)
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%d.%m.%y')
        data['amount'] = data['amount'].round(2)
        data.columns = data.columns.str.capitalize()
        data['Type'] = data['Type'].str.capitalize()
        data['Description'] = data['Description'].str.capitalize()
        return data




if __name__ == '__main__':
    z = DataPackage()
    z1 = z.cleaned_data()
