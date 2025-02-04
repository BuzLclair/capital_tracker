import pandas as pd

from Longterm_investment.services.collections import cash_flows_service



class DataPackage:

    def __init__(self):
        self.cash_flows_object = cash_flows_service.CashFlowService()
        self.data = self.cash_flows_object.main_collection.document_query({})


    def cleaned_data(self):
        data = self.data[['date', 'type', 'amount', 'platform', 'currency', 'description']].copy()
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
        return data




if __name__ == '__main__':
    z = DataPackage()
    z1 = z.cleaned_data()
