import dash
import dash_bootstrap_components as dbc

from dash import html, dcc
from dash.dependencies import Input, Output
from Longterm_investment.gui.dashboard_utils import category_element_layout, category_element_layout2
from Longterm_investment.services.data_bridge import DataPackage, global_balance_chart, PlatformSplitChart, asset_balance_chart




app = dash.Dash(__name__)
app.title = 'Capital Tracker'


data_package_object = DataPackage(simul=True)
aggregated_data_package = data_package_object.aggregated_package
currency_data_package = data_package_object.currency_packaging()
platform_data_package = data_package_object.platform_packaging()
asset_data_package = data_package_object.asset_class_packaging()

global_balance_fig = global_balance_chart(aggregated_data_package['consolidated_balance'])
platform_split_fig_object = PlatformSplitChart(platform_data_package)
asset_balance_fig = asset_balance_chart(asset_data_package['historical_amount_pct'], asset_data_package['value_names'], asset_data_package['asset_colors'])








app.layout = html.Div(className='dashboard', children=[


    html.Div(className='navigation-pane-container', children=[
        html.Div(className='title-block', children=[
            html.Img(className='logo-capital-tracker', src='assets/logo-capital-tracker.png')
            ]),


        dcc.Tabs(id='navigation-pane-value', value='accounts', vertical=True, style=None, className='navigation-pane', children=[



            dcc.Tab(label='Overview', value='overview', className='navigation-box overview', selected_className='tab--selected overview-selected', children=[
                html.Div(className='main-page overview', children=[


                    html.Div(className='overview-box total-capital', children=[
                        html.Div(className='box-title total-capital', children=['Total Capital']),
                        html.Div(className='box-content total-capital ', children=[
                            html.Div(className='total-portolio-icon total-capital', children=[]),
                            html.Div(className='total-portolio-value-box total-capital', children=[
                                html.Div(className='total-portolio-value-box-main total-capital', children=['{:,}'.format(int(aggregated_data_package['consolidated_balance'].iloc[-1])).replace(",", "'")]),
                                html.Div(className='total-portolio-value-box-growth total-capital', children=[aggregated_data_package['last_month_growth']]),
                                ]),
                            ])
                        ]),


                    html.Div(className='overview-box account-breakdown', children=[
                        html.Div(className='box-title account-breakdown', children=['Account Breakdown']),
                        html.Div(className='box-content account-breakdown', children=
                                 [category_element_layout2(platform_name, platform_data_package, platform_split_fig_object, category_name='platform') for platform_name in platform_data_package['value_amount'].keys()]
                             ),
                        ]),


                    html.Div(className='overview-box currency-exposure', children=[
                        html.Div(className='box-title currency-exposure', children=['Currency Exposure']),
                        html.Div(className='box-content currency-exposure', children=
                                [category_element_layout(ccy_ticker, currency_data_package, category_name='currency') for ccy_ticker in currency_data_package['value_amount'].keys()]
                            ),
                        ]),


                    html.Div(className='overview-box asset-segmentation', children=[
                        html.Div(className='box-title asset-segmentation', children=['Asset Segmentation']),
                        html.Div(className='box-content asset-segmentation', children=[
                                dcc.Graph(id='_asset-segmentation-chart', className='asset-segmentation-chart', figure=asset_balance_fig, config={'responsive': True, 'displayModeBar': False})
                            ]),
                        ]),


                    html.Div(className='overview-box capital-trend', children=[
                        html.Div(className='box-title capital-trend', children=['Capital Trend']),
                        html.Div(className='box-content capital-trend', children=[
                            html.Div(className='capital-trend-chart-box', children=[
                                html.Div(className='capital-trend-timeline', children=[
                                    dbc.RadioItems(id='_capital-trend-timeline', className='capital-trend-timeline-radio', options={'3M':'3M', '6M':'6M', '1Y':'1Y', '3Y':'3Y', 'ALL':'ALL'}, value='1Y',
                                                   inputClassName="capital-trend-timeline-radio-input", labelClassName="capital-trend-timeline-radio-label",)]),
                                dcc.Graph(id='_capital-trend-chart', className='capital-trend-chart', figure=global_balance_fig, config={'responsive': True, 'displayModeBar': False})]),
                            ])
                        ]),

                    ])
                ]),






            dcc.Tab(label='Accounts', value='accounts', className='navigation-box accounts', selected_className='tab--selected accounts-selected', children=[

                html.Div(className='main-page accounts', children=[
                    dcc.Tabs(id='accounts-tabs-value', value='financial_snapshot', vertical=False, style=None, className='accounts-tabs', children=[

                        dcc.Tab(label='Financial snapshot', value='financial_snapshot', className='accounts-box snapshot', selected_className='tab--selected snapshot-selected', children=[]),
                        dcc.Tab(label='Transactions', value='transactions', className='accounts-box transactions', selected_className='tab--selected transactions-selected', children=[]),
                        dcc.Tab(label='Balance sheet', value='balance_sheet', className='accounts-box balancesheet', selected_className='tab--selected balancesheet-selected', children=[]),


                        ]),
                    ]),
                ]),



            dcc.Tab(label='Filler2', value='filler2', className='navigation-box filler2', selected_className='tab--selected filler2-selected', children=[
                ]),


            dcc.Tab(label='Filler3', value='filler3', className='navigation-box filler3', selected_className='tab--selected filler3-selected', children=[
                ]),
            ])



        ])
    ])













@app.callback(
    Output(component_id='_capital-trend-chart', component_property='figure'),
    Input(component_id='_capital-trend-timeline', component_property='value'))
def update_capital_trend_figure(timeline):
    timeline_dict = {'3M':90, '6M': 180, '1Y':365, '3Y':1095, 'ALL':1000000}
    timeline_pick = timeline_dict[timeline]
    updated_data_package = aggregated_data_package['consolidated_balance'].iloc[-timeline_pick:]
    fig = global_balance_chart(updated_data_package)
    return fig









if __name__ == '__main__':
    app.run(debug=False)
    print('Running on http://127.0.0.1:8050/')
