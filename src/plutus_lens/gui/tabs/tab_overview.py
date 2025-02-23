import dash_bootstrap_components as dbc

from dash import html, dcc
from src.plutus_lens.gui.dashboard_utils import category_element_layout, category_element_layout2






def get_overview_tab_layout(aggregated_data_package, platform_data_package, platform_split_fig_object,
                            currency_data_package, asset_balance_fig, global_balance_fig):
    return html.Div(className='main-page overview', children=[

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
