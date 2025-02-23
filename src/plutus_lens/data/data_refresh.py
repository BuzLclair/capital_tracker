from platform_data.platform_data_refresh import CapitalVaultDataFeed
from market_data.market_data_extract import ForexData, SecuritiesData


def main():
    CapitalVaultDataFeed().data_feed(update=True)
    ForexData().update_fx_data()
    SecuritiesData().update_market_data()




if __name__ == '__main__':
    main()
