from dash import html, dcc

from src.plutus_lens.gui.tabs import tab_overview, tab_accounts
from src.plutus_lens.gui.utils.data_loader import *


def create_layout():
    return html.Div(className='dashboard', children=[

        html.Div(className='flex-container-column-starts navigation-pane-container', children=[
            html.Div(className='title-block flex-container-row-center', children=[
                html.Img(className='logo-capital-tracker', src='assets/icons/logo-capital-tracker.png')
                ]),

            dcc.Tabs(id='navigation-pane-value', value='accounts', vertical=True, style=None, className='flex-container-column-starts navigation-pane', children=[

                dcc.Tab(label='Overview', value='overview', className='navigation-box nav-box-overview',
                        selected_className='navigation-box--selected nav-box-overview--selected', children=[
                            tab_overview.get_overview_tab_layout(aggregated_data_package, platform_data_package, platform_split_fig_object,
                                                        currency_data_package, asset_balance_fig, global_balance_fig)
                            ]),

                dcc.Tab(label='Accounts', value='accounts', className='navigation-box nav-box-accounts',
                        selected_className='navigation-box--selected nav-box-accounts--selected', children=[
                            tab_accounts.get_accounts_tab_layout(snapshot_data, snapshot_charts_object, accounts_split_data, transactions_data)
                            ]),

                dcc.Tab(label='Filler2', value='filler2', className='navigation-box nav-box-filler2',
                        selected_className='navigation-box--selected nav-box-filler2--selected', children=[]),

                dcc.Tab(label='Filler3', value='filler3', className='navigation-box nav-box-filler3',
                        selected_className='navigation-box--selected nav-box-filler3--selected', children=[]),
                ])
            ])
        ])



