from dash import html, dcc

from src.plutus_lens.services._services_utils import clean_pct_number


def category_element_layout(value_ticker, value_data_package, category_name):
    return html.Div(className=f'{category_name}-exposure-element', children=[

        html.Div(className=f'{category_name}-exposure-element-group1', children=[
            html.Div(className=f'{category_name}-exposure-element-icon', style={'backgroundImage': f"url('assets/icons/icon-{category_name}-{value_ticker}.png')", 'backgroundRepeat': 'no-repeat'}),
            html.Div(className=f'{category_name}-exposure-element-primary-text-box', children=[
                html.Div(className=f'{category_name}-exposure-element-primary-text-ticker', children=[value_ticker]),
                html.Div(className=f'{category_name}-exposure-element-primary-text-name', children=[value_data_package['value_names'][value_ticker]]),
                ]),
            html.Div(className=f'{category_name}-exposure-element-primary-text-box', children=[value_data_package['value_amount'][value_ticker]]),
            ]),

        html.Div(className=f'{category_name}-exposure-element-bar-container', children=[
            html.Div(className=f'{category_name}-exposure-element-pct-bar-empty'),
            html.Div(className=f'{category_name}-exposure-element-pct-bar', style={'width': value_data_package['value_amount_pct_of_total'][value_ticker]}),
            ]),

        html.Div(className=f'{category_name}-exposure-element-group2', children=[
            html.Div(className=f'{category_name}-exposure-element-pct-value', children=[value_data_package['value_amount_pct_of_total'][value_ticker]]),
            html.Div(className=f'{category_name}-exposure-element-pct-change', children=[value_data_package['value_amount_change'][value_ticker]]),
            ]),
        ])



def category_element_layout2(value_ticker, value_data_package, chart_object, category_name):
    return html.Div(className=f'{category_name}-exposure-element', children=[

        html.Div(className=f'{category_name}-exposure-element-group1', children=[
            html.Div(className=f'{category_name}-exposure-element-primary-text-box', children=[
                html.Div(className=f'{category_name}-exposure-element-primary-text-ticker', children=[value_ticker]),
                html.Div(className=f'{category_name}-exposure-element-primary-text-name', children=[value_data_package['value_names'][value_ticker]]),
                ]),
            html.Div(className=f'{category_name}-exposure-element-icon', style={'backgroundImage': f"url('assets/icons/icon-{category_name}-{value_ticker}.png')", 'backgroundRepeat': 'no-repeat'}),
            ]),

        html.Div(className=f'{category_name}-exposure-element-total-amount', children=[value_data_package['value_amount'][value_ticker]]),


        html.Div(className=f'{category_name}-exposure-element-charts-section', children=[
            html.Div(className=f'{category_name}-exposure-element-trend-chart-box', children=[
                dcc.Graph(id=f'_{category_name}-trend-chart-{value_ticker}', className=f'{category_name}-trend-chart', figure=chart_object.create_trend_chart(value_ticker), config={'responsive': False, 'displayModeBar': False}),
                html.Div(className=f'{category_name}-trend-text', children=[value_data_package['value_amount_change'][value_ticker]]),
                ]),

            html.Div(className=f'{category_name}-exposure-element-split-chart-box', children=[
                html.Div(className=f'{category_name}-split-text', children=[f"{value_data_package['value_amount_pct_of_total'][value_ticker]}"]),
                dcc.Graph(id=f'_{category_name}-split-chart-{value_ticker}', className=f'{category_name}-split-chart', figure=chart_object.create_pie_chart(value_ticker), config={'responsive': False, 'displayModeBar': False}),
                ]),
            ]),
        ])



def category_element_layout3(data, platform_name):
    return html.Div(className=f'cash-section-credit-card content-cash_overview-split-section-{platform_name}-block', style={'backgroundImage': f"url('assets/images/account-card-{platform_name}.svg')", 'backgroundRepeat': 'no-repeat'}, children=[

        html.Div(className=f'cash-section-main-title content-cash_overview-split-section-{platform_name}-block-title', children=[platform_name], style={'color': data[platform_name]['color'].replace(', 1)', ', 0.95)')}),

        html.Div(className=f'cash-section-main-cash-section content-cash_overview-split-section-{platform_name}-block-cash-section', children=[
            html.Div(className=f'cash-section-main-cash-block1 cash-section-main-cash-section content-cash_overview-split-section-{platform_name}-block-cash-section-1', children=[
                html.Div(className=f'cash-section-main-cash-title content-cash_overview-split-section-{platform_name}-block-cash-section-title', children=['Available Cash']),
                html.Div(className=f'cash-section-main-cash-amount content-cash_overview-split-section-{platform_name}-block-cash-section-amount', children=['{:,}'.format(int(data[platform_name]['available_cash'])).replace(",", "'")]),
                ]),
            html.Div(className=f'cash-section-main-cash-change content-cash_overview-split-section-{platform_name}-block-cash-section-change', children=[data[platform_name]['delta_cash_since_pm'] + " since previous month"]),
            ]),

        html.Div(className=f'content-cash_overview-split-section-{platform_name}-block-stats', children=[
            html.Div(className=f'content-cash_overview-split-section-{platform_name}-block-stats-transactions', children=[]),

            html.Div(className=f'content-cash_overview-split-section-{platform_name}-block-stats-repartition', children=[]),
            ]),

        ])





