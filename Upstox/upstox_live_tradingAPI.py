#### Import the upstock sdk
# from upstox_api.api import Upstox, TransactionType, OrderType, ProductType, Exchange
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import upstox_client
from upstox_client.rest import ApiException


class UpstoxAPILive:
    def __init__(self, access_token):
        # //Need to connect to Upstox with access token
        configuration = upstox_client.Configuration()
        configuration.access_token = access_token
        self.api_version = '2.0'
        self.user_api_instance = upstox_client.UserApi(upstox_client.ApiClient(configuration))
        self.portfolio_api_instance = upstox_client.PortfolioApi(upstox_client.ApiClient(configuration))
        self.intraday_instance = upstox_client.HistoryApi(upstox_client.ApiClient(configuration))
        self.order_instance = upstox_client.OrderApi(upstox_client.ApiClient(configuration))
        self.timeframes_mapping = {
            "1-minute": 1,
            "2-minutes": 2,
            "3-minutes": 3,
            "4-minutes": 4,
            "5-minutes": 5,
            "6-minutes": 6,
            "10-minutes": 10,
            "12-minutes": 12,
            "15-minutes": 15,
            "30-minutes": 30,
            "1-hour": 60,
            "2-hours": 120,
            "3-hours": 180,
            "4-hours": 240,
            "6-hours": 360,
            "8-hours": 480,
            "12-hours": 720,
            "1-day": 1440,
        }

    def get_profile(self):
        try:
            return self.user_api_instance.get_profile(self.api_version)
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None

    def get_balance(self):
        try:
            balance = self.user_api_instance.get_user_fund_margin(self.api_version, segment='SEC').to_dict()
            return balance['data']['equity']['available_margin']
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return None

    def get_positions(self):
        try:
            return self.portfolio_api_instance.get_positions(self.api_version)
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return None

    def place_order(
            self, transaction_type, symbol, quantity):

        body = upstox_client.PlaceOrderRequest(quantity, "D", "DAY", 0.0, "string", symbol,
                                               "MARKET", transaction_type, 0,
                                               0.0, False)

        try:
            api_response = self.order_instance.place_order(body, self.api_version)
            print(api_response)
        except ApiException as e:
            print("Exception when calling OrderApi->place_order: %s\n" % e)

    # def get_verification_time(self, timeframe: int):
    #     """
    #     Generate a list of verification times based on the given timeframe in minutes.
    #
    #     :param timeframe: Timeframe in minutes
    #     :return: List of verification times
    #     """
    #     # Initialize the start time to just before midnight on January 1, 2021
    #     start_time = datetime(year=2021, month=1, day=1, hour=0, minute=0) - timedelta(seconds=2)
    #
    #     # Set the end time to just before midnight on January 1, 2021
    #     end_time = datetime(year=2021, month=1, day=1, hour=23, minute=59, second=59)
    #
    #     # Initialize the list of verification times with the start time
    #     time_list = [start_time.strftime("%H:%M:%S")]
    #
    #     # Set the current time to the start time
    #     current_time = start_time
    #
    #     # Loop to generate verification times at intervals of the given timeframe
    #     while current_time <= end_time:
    #         current_time += timedelta(minutes=timeframe)
    #         time_list.append(current_time.strftime("%H:%M:%S"))
    #
    #     # Remove the first and last elements from the list
    #     del time_list[0]
    #     del time_list[-1]
    #
    #     # Return the list of verification times
    #     return time_list

    def get_rates(self, symbol, interval="30minute"):
        """
        Fetch live intraday data for a given symbol and timeframe.

        :param symbol: Trading symbol
        :param interval: Timeframe for the data
        :return: DataFrame of historical data
        """
        try:
            api_response = self.intraday_instance.get_intra_day_candle_data(symbol, interval,
                                                                            self.api_version).to_dict()
            return api_response['data']['candles']
        except Exception as e:
            print(f"Error fetching intra-day candle data: {e}")
            return None

    def resume(self):
        """
        Retrieve current open positions.

        :return: DataFrame of open positions
        """
        try:
            positions = self.get_positions()
            columns_list = ["trading_symbol", "quantity", "average_price", "last_price", "pnl"]
            summary = pd.DataFrame(positions, columns=columns_list)
            return summary
        except Exception as e:
            print(f"Error fetching open positions: {e}")

    def run(
            self, symbol, buy, sell, lot
    ):
        """
        Execute the trading logic, including opening and closing positions.

        :param symbol: Trading symbol
        :param buy: Buy signal
        :param sell: Sell signal
        :param lot: Lot size
        :param pct_tp: Take profit percentage
        :param pct_sl: Stop loss percentage
        :param comment: Order comment
        :param magic: Magic number for the order
        """
        print("------------------------------------------------------------------")
        print(
            "Date: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\tSYMBOL:", symbol
        )

        # Retrieve current open positions
        orders = self.resume()
        print(f"BUY: {buy} \t  SELL: {sell}")

        position = None
        identifier = None

        # Check if there are any open positions for the given symbol
        if not orders.empty:
            position_list = orders.loc[orders["symbol"] == symbol]
            if not position_list.empty:
                position = position_list.iloc[0]["quantity"]
                identifier = position_list.iloc[0]["symbol"]

        # Print the current position and identifier if available
        if position is not None:
            print(f"POSITION: {position} \t ID: {identifier}")

        # Logic to close buy position if buy signal is true and no position is open
        if buy and position == 0:
            buy = False
        elif not buy and position == 0:
            # self.place_order(
            #     TransactionType.Sell, symbol, lot, comment=comment, magic=magic
            # )
            print(f"CLOSE BUY POSITION")

        # Logic to close sell position if sell signal is true and a position is open
        if sell and position == 1:
            sell = False
        elif not sell and position == 1:
            # self.place_order(
            #     TransactionType.Buy, symbol, lot, comment=comment, magic=magic
            # )
            print(f"CLOSE SELL POSITION")

        # Logic to open buy position if buy signal is true
        if buy:
            # self.place_order(
            #     TransactionType.Buy, symbol, lot, comment=comment, magic=magic
            # )
            print(f"OPEN BUY POSITION")

        # Logic to open sell position if sell signal is true
        if sell:
            # self.place_order(
            #     TransactionType.Sell, symbol, lot, comment=comment, magic=magic
            # )
            print(f"OPEN SELL POSITION")

        print("------------------------------------------------------------------")

        print("------------------------------------------------------------------")
