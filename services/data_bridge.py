import random
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from Longterm_investment.services._services_utils import clean_pct_number
from Longterm_investment.services.portfolio_service import PortfolioService




class DataPackage:

    def __init__(self, simul):
        self.portfolio_object = PortfolioService()
        self.balance_ccy = self.portfolio_object.balance_by_currency()
        self.balance_platform = self.portfolio_object.balance_by_platform()
        self.balance_aggreg = self.portfolio_object.balance_total()
        self.balance_asset_class = self.portfolio_object.balance_by_asset_class()

        self.create_simulated_numbers(simul)
        self.aggregated_package = self.aggregated_packaging()


    def create_simulated_numbers(self, simul):
        if simul:
            random_nb = random.random()*9.7 + 0.3
            self.balance_ccy *= random_nb
            self.balance_platform *= random_nb
            self.balance_aggreg *= random_nb
            self.balance_asset_class *= random_nb



    def aggregated_packaging(self):
        conso_monthly_pct = self.balance_aggreg.resample('ME').last().pct_change()
        last_month_growth = clean_pct_number(conso_monthly_pct.iloc[-1], '', '% since last month')

        self.balance_platform.rename(columns={'Interactive Brokers': 'IBKR'}, inplace=True)

        package = {'currency_balances': self.balance_ccy, 'consolidated_balance': self.balance_aggreg, 'platform_balances': self.balance_platform, 'asset_balances': self.balance_asset_class,
                   'conso_monthly_pct_change': conso_monthly_pct, 'last_month_growth': last_month_growth}
        return package


    def _packaging(self, category_name, value_names):
        last_months_data = self.aggregated_package[category_name].copy().resample('ME').last().iloc[-2:,:].replace(0, np.nan)
        last_months_data.dropna(how='all', axis=1, inplace=True)

        value_pct_of_total = last_months_data.div(last_months_data.sum(axis=1), axis=0)

        value_change_since_prev_month = last_months_data.pct_change().dropna()
        # value_change_since_prev_month = (value_pct_of_total - value_pct_of_total.shift(1)).dropna()
        value_change_since_prev_month = value_change_since_prev_month.apply(lambda x: clean_pct_number(x.iloc[0], '', '% since last month'))

        value_amount = dict(last_months_data.iloc[-1].astype(int).apply(lambda x: f'{x:,.0f}'.replace(',', "'")))
        value_amount_sorted = dict(sorted(value_amount.items(), key=lambda item: int(item[1].replace("'", '')), reverse=True))

        package = {'value_amount': value_amount_sorted, 'value_amount_pct_of_total': dict(value_pct_of_total.iloc[-1].apply(lambda x: f'{round(100*x, 2)}%')), 'value_amount_change': dict(value_change_since_prev_month),
                   'value_names': value_names}
        return package


    def currency_packaging(self):
        ccy_names = {'CHF':'Swiss Franc', 'USD':'United States Dollar', 'EUR':'Euro', 'AUD':'Australian Dollar', 'HKD':'Hong Kong Dollar', 'NZD':'New Zealand Dollar', 'GBP':'British Pound Sterling'}
        package = self._packaging('currency_balances', ccy_names)
        return package


    def platform_packaging(self):
        platform_names = {'IBKR':'Interactive Brokers', 'Etoro':'eToro Group Ltd', 'BCGE':'Banque cantonale de Genève', 'Kraken':'Payward Limited', 'Revolut':'Revolut Ltd'}
        package = self._packaging('platform_balances', platform_names)
        package['platform_colors'] = {'IBKR': 'rgba(0, 0, 0, 1)', 'Etoro': 'rgba(73, 200, 41, 1)', 'BCGE': 'rgba(224, 35, 48, 1)',
                                      'Kraken': 'rgba(95, 56, 220, 1)', 'Revolut': 'rgba(255, 255, 255, 1)'}
        package['historical_amount'] = self.balance_platform.iloc[-30:,:]
        return package


    def asset_class_packaging(self):
        asset_names = {'cash_flows':'Cash', 'cryptos':'Crypto', 'securities':'Equities', 'fixed_income':'Bonds'}
        package = self._packaging('asset_balances', asset_names)

        package['historical_amount'] = self.balance_asset_class.iloc[-90:,:]
        package['historical_amount_pct'] = (100 * package['historical_amount'].div(package['historical_amount'].sum(axis=1), axis=0)).round(0)

        package['asset_colors'] = {'Cash': 'rgba(140, 148, 161, 1)', 'Crypto': 'rgba(150, 190, 240, 1)', 'Equities': 'rgba(50, 100, 180, 1)', 'Bonds': 'rgba(58, 66, 75, 1)'}
        return package






def global_balance_chart(data):
    space_formatted_data = data.apply(lambda x: f'{x:,.0f}'.replace(',', ' '))

    fig = px.line(data, line_shape='spline')
    fig.update_traces(line=dict(color='rgba(50, 100, 180, 1)'), fill='tozeroy', fillcolor='rgba(50, 100, 180, 0.2)',
                      hovertemplate='<b>Date:</b> %{x}<br><b>Amount:</b> %{customdata} CHF<extra></extra>', customdata=space_formatted_data.values)
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0), xaxis_title=None, yaxis_title='Amount (CHF)',
                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(86, 95, 106, 0.7)', gridwidth=0.1, griddash='dash', ticklabelstandoff=10, zeroline=False,
                                                             range=[0.95*min(data), 1.05*max(data)]), hoverlabel=dict(bgcolor='rgba(140, 148, 161, 1)', font=dict(family='Helvetica', size=10, color='rgba(58, 66, 75, 1)'),
            bordercolor='rgba(0,0,0,0)'))
    return fig



class PlatformSplitChart:
    def __init__(self, data_dict):
        self.sorted_pct_data = dict(sorted(data_dict['value_amount_pct_of_total'].items(), key=lambda item: item[1], reverse=True))
        self.sorted_colors = {key: data_dict['platform_colors'][key] for key in self.sorted_pct_data}
        self.pct_data_float = {key: round(float(value.split('%')[0])/100, 4) for key, value in self.sorted_pct_data.items()}

        self.historical_amount_dict = dict(data_dict['historical_amount'])


    def create_pie_chart(self, current_platform):
        slice_to_pull_idx = list(self.pct_data_float.keys()).index(current_platform)
        pull = [0.2 if element == slice_to_pull_idx else 0 for element in range(len(self.pct_data_float))]

        colors = list(self.sorted_colors.values())
        colors = [color.replace(', 1)', ', 0.75)') for color in colors]

        fig = go.Figure(data=[go.Pie(labels=list(self.pct_data_float.keys()), values=list(self.pct_data_float.values()), pull=pull, textinfo='none', hole=.83,
                                     hoverinfo='none', marker=dict(colors=colors))])
        fig.update_layout(showlegend=False, xaxis=dict(showline=False, showgrid=False, zeroline=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          yaxis=dict(showline=False, showgrid=False, zeroline=False), margin=dict(t=0, b=0, l=0, r=0))
        return fig


    def create_trend_chart(self, current_platform):
        chart_data = self.historical_amount_dict[current_platform]
        chart_color = self.sorted_colors[current_platform]
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


def asset_balance_chart(data, data_names, chart_color):
    space_formatted_data = data.map(lambda x: f'{int(x)}%')
    space_formatted_data.index = space_formatted_data.index.strftime('%d.%m.%y')
    data.rename(columns=data_names, inplace=True)

    fig = go.Figure()
    for col in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, line=dict(color=chart_color[col]), stackgroup='one', groupnorm='percent'))

    fig.update_traces(hovertemplate='<b>Date:</b> %{customdata[0]}<br><i>Cash:</i> %{customdata[1]}, <i>Equities:</i> %{customdata[2]}, <br><i>Cryptos:</i> %{customdata[3]}, <i>Bonds:</i> %{customdata[4]}<extra></extra>',
                      customdata=list(zip(space_formatted_data.index, space_formatted_data['cash_flows'], space_formatted_data['securities'], space_formatted_data['cryptos'], space_formatted_data['fixed_income'])))
    fig.update_layout(showlegend=True, legend=dict(orientation="h", font=dict(size=8), title_text='', borderwidth=0),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=0), xaxis_title=None, yaxis_title=None,
                      xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, 100]),
                      hoverlabel=dict(bgcolor='rgba(140, 148, 161, 1)', font=dict(family='Helvetica', size=10, color='rgba(58, 66, 75, 1)'),
            bordercolor='rgba(0,0,0,0)'))
    return fig



