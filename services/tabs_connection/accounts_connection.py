import pandas as pd
import plotly.express as px


from Longterm_investment.services._services_utils import clean_pct_number
from Longterm_investment.services.collections import cash_flows_service
from Longterm_investment.services.portfolio_service import PortfolioService





class DataPackage:

    def __init__(self):
        self.cash_flows_object = cash_flows_service.CashFlowService()

        self.data = self.cash_flows_object.main_collection.document_query({})
        self.cash_history = self.cash_flows_object.balance_aggregated()
        self.platform_colors = {'Interactive Brokers': 'rgba(216, 18, 34, 1)', 'Etoro': 'rgba(19, 198, 54, 1)', 'BCGE': 'rgba(239, 46, 49, 1)',
                                      'Kraken': 'rgba(95, 56, 220, 1)', 'Revolut': 'rgba(0, 0, 0, 1)'}


    def cleaned_data(self):
        data = self.data[['platform', 'type', 'date', 'currency', 'amount', 'description']].copy()
        data = data.sort_values(by='date', ascending=False)
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%d.%m.%y')
        data['amount'] = data['amount'].round(2)
        data.columns = data.columns.str.capitalize()
        data['Type'] = data['Type'].str.capitalize()
        data['Description'] = data['Description'].str.capitalize()
        return data


    def __create_data_package(self, data_object):
        data_dict = dict()
        balance_aggreg = data_object.balance_aggregated().copy()
        data_dict['total_cash'] = balance_aggreg

        conso_monthly_pct = balance_aggreg.resample('ME').last().pct_change()
        last_month_growth = clean_pct_number(conso_monthly_pct.iloc[-1], '', '% since last month')
        data_dict['last_month_growth'] = last_month_growth

        balance_asset_class = PortfolioService().balance_by_asset_class()
        value_pct_of_total = balance_asset_class.div(balance_asset_class.sum(axis=1), axis=0)['cash_flows']
        value_pct_of_total_clean = clean_pct_number(value_pct_of_total.iloc[-1], '', '% of total capital')[1:]
        data_dict['value_amount_pct_of_total'] = value_pct_of_total_clean
        return data_dict


    def snapshot_data(self):
        data = self.__create_data_package(self.cash_flows_object)
        return data


    def __create_acount_individual_package(self, data_cash, platform_name):
        data_dict = dict()
        data_monthly = data_cash.resample('ME').last()
        data_dict['available_cash'] = data_monthly.iloc[-1]
        delta_cash_since_pm = (data_monthly - data_monthly.shift(1)).iloc[-1]
        if delta_cash_since_pm < 0:
            number_as_txt = f"{int(delta_cash_since_pm):,}".replace(",", "'")
        else:
            number_as_txt = f"+{int(delta_cash_since_pm):,}".replace(",", "'")
        data_dict['delta_cash_since_pm'] = number_as_txt
        data_dict['color'] = self.platform_colors[platform_name]
        return data_dict


    def accounts_split_package(self):
        cash_by_platform = self.cash_flows_object.balance_by_platform()
        data_dict = dict()
        for platform in cash_by_platform.columns:
            data_dict[platform] = self.__create_acount_individual_package(cash_by_platform[platform], platform)

        sorted_dict_desc = dict(sorted(data_dict.items(), key=lambda x: x[1]['available_cash'], reverse=True))
        return sorted_dict_desc




class SnapshotCharts:
    def __init__(self, ):
        pass


    def cash_balance_chart(self, data):
        chart_data = data
        chart_color = 'rgba(34, 65, 125, 1)'
        min_amount, max_amount = min(chart_data), max(chart_data)
        fill_color = chart_color.replace(', 1)', ', 0.2)')
        space_formatted_data = chart_data.apply(lambda x: f'{x:,.0f}'.replace(',', ' '))
        space_formatted_data.index = space_formatted_data.index.strftime('%d.%m.%y')

        fig = px.line(chart_data, line_shape='spline')
        fig.update_traces(line=dict(color=chart_color), fill='tozeroy', fillcolor=fill_color, hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]} CHF<extra></extra>',
                          customdata=list(zip(space_formatted_data.index, space_formatted_data.values)))
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0), xaxis_title=None, yaxis_title=None,
                          xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0.99*min_amount, 1.01*max_amount]),
                          hoverlabel=dict(bgcolor='rgba(140, 148, 161, 1)', font=dict(family='Helvetica', size=8, color='rgba(58, 66, 75, 1)'),
                                          bordercolor='rgba(0,0,0,0)'))
        return fig








if __name__ == '__main__':
    z = DataPackage()
    z1 = z.accounts_split_package()

    z2 = z.data.loc[~z.data['type'].isin(['Expense'])]
    z3 = z2['type'].unique()


