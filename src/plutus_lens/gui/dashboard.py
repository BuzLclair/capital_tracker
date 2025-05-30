import dash
import dash_bootstrap_components as dbc

from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
from src.plutus_lens.gui.dashboard_utils import category_element_layout, category_element_layout2, category_element_layout3

from src.plutus_lens.services.tabs_connection.overview_connection import DataPackage, global_balance_chart, PlatformSplitChart, asset_balance_chart
from src.plutus_lens.services.tabs_connection import accounts_connection



app = dash.Dash(__name__)
app.title = 'Capital Tracker'



# Overview
data_package_object = DataPackage(simul=True)
aggregated_data_package = data_package_object.aggregated_package
currency_data_package = data_package_object.currency_packaging()
platform_data_package = data_package_object.platform_packaging()
asset_data_package = data_package_object.asset_class_packaging()

global_balance_fig = global_balance_chart(aggregated_data_package['consolidated_balance'])
platform_split_fig_object = PlatformSplitChart(platform_data_package)
asset_balance_fig = asset_balance_chart(asset_data_package['historical_amount_pct'], asset_data_package['value_names'], asset_data_package['asset_colors'])


# Accounts
accounts_object = accounts_connection.DataPackage()

snapshot_data = accounts_object.snapshot_data()
snapshot_charts_object = accounts_connection.SnapshotCharts()

accounts_split_data = accounts_object.accounts_split_package()


transactions_data = accounts_object.cleaned_data()








app.layout = html.Div(className='dashboard', children=[


    html.Div(className='flex-container-column-starts navigation-pane-container', children=[
        html.Div(className='title-block flex-container-row-center', children=[
            html.Img(className='logo-capital-tracker', src='assets/logo-capital-tracker.png')
            ]),


        dcc.Tabs(id='navigation-pane-value', value='accounts', vertical=True, style=None, className='flex-container-column-starts navigation-pane', children=[



            dcc.Tab(label='Overview', value='overview', className='navigation-box nav-box-overview', selected_className='navigation-box--selected nav-box-overview--selected', children=[
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





            dcc.Tab(label='Accounts', value='accounts', className='navigation-box nav-box-accounts', selected_className='navigation-box--selected nav-box-accounts--selected', children=[

                html.Div(className='main-page accounts', children=[
                    dcc.Tabs(id='accounts-tabs-value', value='financial_snapshot', vertical=False, style=None, className='accounts-tabs', children=[


                        dcc.Tab(label='Financial snapshot', value='financial_snapshot', className='accounts-box', selected_className='accounts-box--selected snapshot-selected', children=[

                            html.Div(className='snapshot-page', children=[
                                html.Div(className='financial_snapshot_flows_section', children=[
                                    html.Div(className='net_cashflows', children=[
                                        html.Div(className='box-title', children=['Net Cashflows']),
                                        html.Div(className='box-content content-net_cashflows', children=[]),
                                        ]),

                                    html.Div(className='financial_snapshot_flows_details', children=[
                                        html.Div(className='income_profile', children=[
                                            html.Div(className='box-title', children=['Income Profile']),
                                            html.Div(className='box-content content-income_profile', children=[]),
                                            ]),

                                        html.Div(className='expense_breakdown', children=[
                                            html.Div(className='box-title', children=['Expense Breakdown']),
                                            html.Div(className='box-content content-expense_breakdown', children=[
                                                html.Div(className='content-expense_breakdown_big_4-first', children=[
                                                    html.Div(className='content-expense_breakdown_big_4-1', children=['Fixed / variable exp.']),
                                                    html.Div(className='content-expense_breakdown_big_4-2', children=['% Split']),
                                                    ]),
                                                html.Div(className='content-expense_breakdown_big_4-second', children=[
                                                    html.Div(className='content-expense_breakdown_big_4-3', children=['Nb by month']),
                                                    html.Div(className='content-expense_breakdown_big_4-4', children=['Avg by month']),
                                                    ]),
                                                html.Div(className='content-expense_breakdown_prev_month', children=['PM'])

                                                ]),
                                            ]),
                                        ]),
                                    ]),






                                html.Div(className='cash_overview', children=[
                                    html.Div(className='box-title', children=['Cash Overview']),
                                    html.Div(className='box-content content-cash_overview', children=[

                                        html.Div(className='content-cash_overview-aggregated-section', children=[
                                            html.Div(className='content-cash_overview-aggregated-section-block1', children=[
                                                html.Div(className='content-cash_overview-aggregated-section-block1-subsection1', children=[
                                                    html.Div(className='content-cash_overview-aggregated-section-block1-subsection1-title', children=['Cash Balance']),
                                                    html.Div(className='content-cash_overview-aggregated-section-block1-subsection1-amount', children=['{:,}'.format(int(snapshot_data['total_cash'].iloc[-1])).replace(",", "'")]),
                                                    ]),
                                                html.Div(className='content-cash_overview-aggregated-section-block1-subsection2', children=[
                                                    dcc.Graph(id='_cash_overview-aggregated-section-chart', className='cash_overview-aggregated-section-chart', figure=snapshot_charts_object.cash_balance_chart(snapshot_data['total_cash'].iloc[-90:]), config={'responsive': False, 'displayModeBar': False})
                                                    ]),
                                                ]),

                                            html.Div(className='content-cash_overview-aggregated-section-block2', children=[
                                                html.Div(className='content-cash_overview-aggregated-section-block2-total_wealth', children=[snapshot_data['value_amount_pct_of_total']]),
                                                html.Div(className='content-cash_overview-aggregated-section-block2-period_change', children=[snapshot_data['last_month_growth']]),
                                                ]),

                                            ]),

                                        html.Div(className='content-cash_overview-split-section', children=[
                                            category_element_layout3(accounts_split_data, platform) for platform in accounts_split_data.keys()
                                            ]),

                                        ]),
                                    ]),

                                ]),
                            ]),






                        dcc.Tab(label='Transactions', value='transactions', className='accounts-box transactions', selected_className='accounts-box--selected transactions-selected', children=[
                            html.Div(className='main-page accounts transactions', children=[

                                html.Div(className='accounts_transactions_filters', children=
                                    [dcc.Dropdown(id=f'accounts_transactions_filters_{column_name}', options=list(transactions_data[column_name].unique()), placeholder=f'Select {column_name}', multi=True, disabled=False)
                                     for column_name in transactions_data.columns]
                                    ),

                                # html.Div(className='accounts_transactions_table', children=dbc.Table.from_dataframe(transactions_data, striped=True, bordered=True, hover=True)),
                                html.Div(className='accounts_transactions_table', children=[dash_table.DataTable(id='accounts_transactions_table_id', data=transactions_data.to_dict('records'),
                                         columns=[{'name': col, 'id': col} for col in transactions_data.columns], page_current=0, page_size=20, page_action='native', fixed_rows={'headers': True})
                                        ])

                                ]),
                            ]),



                        dcc.Tab(label='Balance sheet', value='balance_sheet', className='accounts-box balancesheet', selected_className='accounts-box--selected balancesheet-selected', children=[]),


                        ]),
                    ]),
                ]),







            dcc.Tab(label='Filler2', value='filler2', className='navigation-box nav-box-filler2', selected_className='navigation-box--selected nav-box-filler2--selected', children=[
                ]),


            dcc.Tab(label='Filler3', value='filler3', className='navigation-box nav-box-filler3', selected_className='navigation-box--selected nav-box-filler3--selected', children=[
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
