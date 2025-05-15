from dash.dependencies import Input, Output

from src.plutus_lens.services.tabs_connection.overview_connection import global_balance_chart
from src.plutus_lens.gui.utils.data_loader import aggregated_data_package




def register_callbacks(app):
    @app.callback(
        Output(component_id='_capital-trend-chart', component_property='figure'),
        Input(component_id='_capital-trend-timeline', component_property='value'))
    def update_capital_trend_figure(timeline):
        timeline_dict = {'3M':90, '6M': 180, '1Y':365, '3Y':1095, 'ALL':1000000}
        timeline_pick = timeline_dict[timeline]
        updated_data_package = aggregated_data_package['consolidated_balance'].iloc[-timeline_pick:]
        fig = global_balance_chart(updated_data_package)
        return fig






