from datetime import datetime, timedelta
import time
import pandas as pd
from IntradayDataAppender import IntradayDataAppender


class TradingBot:
    def __init__(self, api, strategy, verifier, symbol, lot, timeframe, pct_tp, pct_sl, prev_close):
        """
      Initialize the TradingBot with the necessary components and trading parameters.

      :param api: Instance of UpstoxAPI for interacting with the Upstox trading platform.
      :param strategy: Instance of TradingStrategy for generating buy and sell signals.
      :param verifier: Instance of TimeframeVerifier for determining verification times.
      :param symbol: str, Trading symbol (e.g., "EURUSD-Z").
      :param lot: float, Lot size for trading.
      :param timeframe: str, Timeframe for trading signals (e.g., "8-hours").
      :param pct_tp: float, Take profit percentage.
      :param pct_sl: float, Stop loss percentage.
      """
        self.api = api
        self.strategy = strategy
        self.verifier = verifier
        self.symbol = symbol
        self.lot = lot
        self.timeframe = timeframe
        self.pct_tp = pct_tp
        self.pct_sl = pct_sl

        # Adding fucntionality to add intraday 30 min data
        self.intraday_data_appender = IntradayDataAppender(api)
        #write logic for previous close
        self.prev_close = prev_close

    def initialize(self):
        """
      Initialize the Upstox API and print account information.

      This method fetches the user profile and account balance from the Upstox API
      and prints them to the console.
      """
        # get auth token from upstox

        try:
            profile = self.api.get_profile()
            print("------------------------------------------------------------------")
            print(f"User ID: {profile['user_id']} \tName: {profile['name']}")
            balance = self.api.get_balance()
            print(f"Balance: {balance['equity']['available_margin']} USD")
            print("------------------------------------------------------------------")
        except Exception as e:
            print(f"Error initializing Upstox: {e}")

    def get_open_positions(self):
        """
      Get current open positions.

      This method fetches the current open positions from the Upstox API and returns them
      as a pandas DataFrame.

      :return: pd.DataFrame, DataFrame containing the current open positions.
      """
        try:
            positions = self.api.get_positions()
            return pd.DataFrame(positions)
        except Exception as e:
            print(f"Error fetching open positions: {e}")
            return pd.DataFrame()

    def run(self, buy, sell, pct_tp=0.0063, pct_sl=0.005, comment="TradingBot", magic=123456):
        """
      Execute trades based on buy and sell signals.

      This method calls the `run` method of the UpstoxAPI instance to place buy or sell orders
      based on the provided signals.

      :param buy: bool, Buy signal.
      :param sell: bool, Sell signal.
      """
        try:
            print("Orchestrating trades in TradingBot...")
            self.api.run(self.symbol, buy, sell, self.lot, self.pct_tp, self.pct_sl)
        except Exception as e:
            print(f"Error executing trades: {e}")

def start_trading(self):
    """
    Start the trading bot and enter the main trading loop.

    This method initializes the Upstox API, reads the flagged stocks from a CSV file,
    and enters a loop where it continuously checks the current time against the trading hours.
    When the current time matches a verification time, it processes each stock in the DataFrame.
    """
    print("Starting trading bot...")
    self.initialize()

    # Read the flagged stocks CSV file
    df_flagged_stocks = pd.read_csv('../Upstox_Data/Buy_Flagged/CCI/flagged_stocks.csv')

    # Define the trading hours and intervals
    start_time = datetime.strptime("09:46:00", "%H:%M:%S").time()
    end_time = datetime.strptime("15:16:00", "%H:%M:%S").time()
    interval = timedelta(minutes=30)

    while True:
        try:
            current_time = datetime.now().time()
            if start_time <= current_time <= end_time and (
                    datetime.combine(datetime.today(), current_time) - datetime.combine(datetime.today(),
                                                                                        start_time)) % interval == timedelta(
                    0):
                print(f"Current time: {current_time.strftime('%H:%M:%S')}")
                for index, row in df_flagged_stocks.iterrows():
                    stock_name = row['Stock Name']
                    last_day_close = row['Last Day Close']
                    take_profit = row['Take Profit']
                    trailing_stop = row['Trailing Stop']
                    # Perform operations for each stock
                    print(f"Processing stock: {stock_name}")

                    # kd logic (need to discuss for buy/sell responsibility segregation)
                    self.intraday_data_appender.append_data_to_dataframe(self.symbol)
                    df_intraday_30min = self.intraday_data_appender.get_dataframe()
                    buy, sell = self.strategy.create_signals(df_intraday_30min)
                    self.run(buy, sell)
                    time.sleep(1)

                time.sleep(60)  # Sleep for a minute to avoid multiple executions within the same minute
            else:
                time.sleep(1)  # Sleep for a second before checking the time again
        except Exception as e:
            print(f"Error in trading loop: {e}")
            time.sleep(1)  # Sleep for a bit before retrying
