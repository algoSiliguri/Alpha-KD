from datetime import datetime
import time
import pandas as pd

class TradingBot:
  def __init__(self, api, strategy, verifier, symbol, lot, timeframe, pct_tp, pct_sl):
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

  def initialize(self):
      """
      Initialize the Upstox API and print account information.

      This method fetches the user profile and account balance from the Upstox API
      and prints them to the console.
      """
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
          self.api.run(self.symbol, buy, sell, self.lot, self.pct_tp, self.pct_sl)
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
      timeframe_condition = self.verifier.get_verification_time(self.timeframe)

      while True:
          try:
              current_time = datetime.now().strftime("%H:%M:%S")
              if current_time in timeframe_condition:
                  print(f"Current time: {current_time}")
                  buy, sell = self.strategy.create_signals(self.symbol, self.timeframe)
                  self.run(buy, sell)
                  time.sleep(1)
          except Exception as e:
              print(f"Error in trading loop: {e}")
              time.sleep(1)  # Sleep for a bit before retrying