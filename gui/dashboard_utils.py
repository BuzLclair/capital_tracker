from dash import html, dcc


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


