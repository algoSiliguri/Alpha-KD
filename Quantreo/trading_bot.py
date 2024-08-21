from datetime import datetime
import time
import traceback
import pandas as pd
from .IntradayDataAppender import IntradayDataAppender

class TradingBot:
  def __init__(self, api, strategy, verifier, symbol, qty, pct_tp, pct_sl, prev_close):
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
      self.qty = qty
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
          profile = self.api.get_profile().to_dict()
          print("------------------------------------------------------------------")
          print(f"User ID: {profile.get('data')['user_id']} \tName: {profile.get('data')['user_name']}")
          balance = self.api.get_balance()
          print(balance)
          print(f"Balance: INR {balance}")
          print("------------------------------------------------------------------")
      except Exception as e:
          traceback.format_exc()
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

  def run(self, buy, sell):
      """
      Execute trades based on buy and sell signals.

      This method calls the `run` method of the UpstoxAPI instance to place buy or sell orders
      based on the provided signals.

      :param buy: bool, Buy signal.
      :param sell: bool, Sell signal.
      """
      try:
          print("Orchestrating trades in TradingBot...")
          # Getting the api to run for sending orders
          self.api.run(self.symbol, buy, sell, self.qty, self.pct_tp, self.pct_sl)
      except Exception as e:
          print(f"Error executing trades: {e}")

  def start_trading(self):
      """
      Start the trading bot and enter the main trading loop.

      This method initializes the Upstox API, fetches the verification times from the TimeframeVerifier,
      and enters a loop where it continuously checks the current time against the verification times.
      When the current time matches a verification time, it generates buy and sell signals and executes trades.
      """
      print("Starting trading bot...")
      self.initialize()
      timeframe_conditions = self.verifier.get_verification_time()
      self.intraday_data_appender.append_data_to_dataframe(self.symbol, initial_run=True)

      while True:
          try:
              # The current time
              current_time = datetime.now()

              # If the time is within the trading time limits
              if timeframe_conditions[1] > current_time > timeframe_conditions[0]:

                  try:

                      self.intraday_data_appender.append_data_to_dataframe(self.symbol)
                      df_intraday_30min = self.intraday_data_appender.get_dataframe()

                      # Managing the signals
                      buy, sell = self.strategy.create_signals(df_intraday_30min)
                      print(f"Buy Signal: {buy}\nSell Signal: {sell}")

                      # Running the order sending mechanism
                      self.run(buy, sell)
                      time.sleep(5)

                  except Exception as e:
                      print(f"Error in main execution: {e}")
          except Exception as e:
              print(f"Error in trading loop: {e}")
              time.sleep(20)  # Sleep for a bit before retrying