#### Import the upstock sdk
# from upstox_api.api import Upstox, TransactionType, OrderType, ProductType, Exchange
from datetime import datetime, timedelta
import json
import time
import pandas as pd
import numpy as np
import upstox_client
import traceback
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
        self.market_data_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))
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

        
        # A flag to check if buy orders are sent for the ticker
        self.buy_order_sent_map: dict = {} # key: symbol, value: order_ids(a list)

    def get_profile(self):
        try:
            return self.user_api_instance.get_profile(self.api_version)
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None

    def get_balance(self):
        try:
            balance = self.user_api_instance.get_user_fund_margin(self.api_version).to_dict()
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
    #     start_time = datetime(year=2021, month=1, day=1, hour=0, minute=0) - timedelta(
    #         seconds=2
    #     )
    #     end_time = datetime(year=2021, month=1, day=1, hour=23, minute=59, second=59)
    #
    #     time_list = [start_time.strftime("%H:%M:%S")]
    #     current_time = start_time
    #     while current_time <= end_time:
    #         current_time += timedelta(minutes=timeframe)
    #         time_list.append(current_time.strftime("%H:%M:%S"))
    #     del time_list[0]
    #     del time_list[-1]
    #
    #     return time_list

    def get_ltp(self, symbol):
        """

        Parameters
        ----------
        symbol: The trading symbol for the ticker

        Returns: The Last Trading Price
        -------

        """
        try:
            instrument_key = self.map_instrument_key(symbol=symbol)
            ltp_response = self.market_data_instance.ltp(instrument_key,self.api_version).to_dict()
            price_data = ltp_response.get("data")
            for key,val in price_data.items():
                return val.get("last_price")

        except Exception as e:
            print(f"Error fetching intra-day candle data: {e}")
            traceback.print_exc()
            return None

    def map_instrument_key(self, symbol, instrument_type = "STK"):
        """
        Maps the instrument key to the respective symbol
        """ 
        # Open and read the instrument key
        if instrument_type == "STK":
            with open('utils/instrumentsData.json', 'r') as file:
                instruments_map = json.load(file) 

            return [i.get(symbol) for i in instruments_map if i.get(symbol)][0]

    def get_last_close(self, symbol):
        try:
            instrument_key = self.map_instrument_key(symbol=symbol)
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            api_response = self.intraday_instance.get_historical_candle_data(instrument_key, "day", yesterday, 
                                                                             self.api_version).to_dict()
            return api_response.get('data').get('candles')[0][4]
        except Exception as e:
            print(f"Error fetching intra-day candle data: {e}")
            traceback.print_exc()
            return None

    def get_rates(self, symbol, interval="30minute"):
        """
        Fetch live intraday data for a given symbol and timeframe.

        :param symbol: Trading symbol
        :param interval: Timeframe for the data
        :return: DataFrame of historical data
        """
        try:
            instrument_key = self.map_instrument_key(symbol=symbol)
            api_response = self.intraday_instance.get_intra_day_candle_data(instrument_key, interval,
                                                                            self.api_version).to_dict()
            return api_response.get('data').get('candles')
        except Exception as e:
            print(f"Error fetching intra-day candle data: {e}")
            traceback.print_exc()
            return None

    def resume(self):
        """
        Retrieve current open positions.

        :return: DataFrame of open positions
        """
        try:
            positions = self.get_positions().to_dict()
            columns_list = ["trading_symbol", "quantity", "average_price", "last_price", "pnl"]
            positions_dict = pd.DataFrame(positions, columns=columns_list)
            return positions_dict
        except Exception as e:
            # traceback.print_exc()
            print(f"Error fetching open positions: {e}")

    def run(
            self, symbol, buy, sell, qty, pct_tp=0.02, pct_sl=0.01, comment="", magic=23400
    ):
        """
        Execute the trading logic, including opening and closing positions.

        :param symbol: Trading symbol
        :param buy: Buy signal
        :param sell: Sell signal
        :param qty: Qty to send order for
        :param pct_tp: Take profit percentage
        :param pct_sl: Stop loss percentage
        :param comment: Order comment
        :param magic: Magic number for the order
        """
        print("----------------------Entering Trade--------------------------------------------")
        print(
            "Date: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\tSYMBOL:", symbol
        )
        positions = self.resume()
        print(f"BUY: {buy} \t  SELL: {sell}")

        # If there are no signals return
        if not buy and not sell:
            print("No signal found")
            return

        # The position and the symbol for the signal
        position = None
        p_symbol = None

        if position:
            if positions.empty:
                position_list = positions.loc[positions["symbol"] == symbol]
                if not position_list.empty:
                    position = position_list.iloc[0]["quantity"]
                    p_symbol = position_list.iloc[0]["symbol"]

                    # The revised qty for the order
                    qty = position - qty

                    # If it is a buy but doesn't have a valid quantity
                    if qty < 0  and buy:
                        return
                    

        # if position is not None:
        #     print(f"POSITION: {position} \t Symbol: {symbol}")

        # if buy and position == 0:
        #     buy = False
        # elif not buy and position == 0:
        #     # self.place_order(
        #     #     TransactionType.Sell, symbol, qty, comment=comment, magic=magic
        #     # )
        #     print(f"CLOSE BUY POSITION")

        # if sell and position == 1:
        #     sell = False
        # elif not sell and position == 1:
        #     # self.place_order(
        #     #     TransactionType.Buy, symbol, qty, comment=comment, magic=magic
        #     # )
        #     print(f"CLOSE SELL POSITION")

        if buy:
            if symbol not in self.buy_order_sent_map.keys():
                # self.place_order(
                #     TransactionType.Buy, symbol, qty, comment=comment, magic=magic
                # )
                self.buy_order_sent_map[symbol] = 1
                print(f"Sent buy order for:{symbol}\t Qty:{qty}\t Transaction type: Buy")
            else:
                # TODO: Cancel the previous order on the same ticker from here
                print("Cancelling the previous order.")
                print(f"Sent buy order for:{symbol}\t Qty:{qty}\t Transaction type: Buy")

        # if sell:
        #     # self.place_order(
        #     #     TransactionType.Sell, symbol, qty, comment=comment, magic=magic
        #     # )
        #     print(f"OPEN SELL POSITION")

        print("------------------------------------------------------------------")
