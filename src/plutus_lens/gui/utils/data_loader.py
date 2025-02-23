from src.plutus_lens.services.tabs_connection.overview_connection import DataPackage, global_balance_chart, PlatformSplitChart, asset_balance_chart
from src.plutus_lens.services.tabs_connection import accounts_connection




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
