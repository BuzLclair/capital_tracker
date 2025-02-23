from dash import html, dcc, dash_table
from src.plutus_lens.gui.dashboard_utils import category_element_layout3






def get_accounts_tab_layout(snapshot_data, snapshot_charts_object, accounts_split_data, transactions_data):
    return html.Div(className='main-page accounts', children=[

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

                    html.Div(className='accounts_transactions_table', children=[dash_table.DataTable(id='accounts_transactions_table_id', data=transactions_data.to_dict('records'),
                             columns=[{'name': col, 'id': col} for col in transactions_data.columns], page_current=0, page_size=20, page_action='native', fixed_rows={'headers': True})
                            ])

                    ]),
                ]),



            dcc.Tab(label='Balance sheet', value='balance_sheet', className='accounts-box balancesheet', selected_className='accounts-box--selected balancesheet-selected', children=[]),


            ]),
        ])
