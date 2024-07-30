from datetime import datetime
import pandas as pd
import time


class TradingBot:
    def __init__(self, api, strategy, verifier, symbol, lot, timeframe, pct_tp, pct_sl):
        """
        Initialize the TradingBot with Upstox API credentials and trading parameters.

        :param api: Instance of UpstoxAPI
        :param strategy: Instance of TradingStrategy
        :param verifier: Instance of TimeframeVerifier
        :param symbol: Trading symbol
        :param lot: Lot size
        :param timeframe: Timeframe for trading signals
        :param pct_tp: Take profit percentage
        :param pct_sl: Stop loss percentage
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

        :return: DataFrame of open positions
        """
        try:
            positions = self.api.get_positions()
            return pd.DataFrame(positions)
        except Exception as e:
            print(f"Error fetching open positions: {e}")
            return pd.DataFrame()

    def run(self, buy, sell):
        """
        Execute trading orders based on buy and sell signals.

        :param buy: Buy signal
        :param sell: Sell signal
        """
        try:
            if buy:
                self.api.place_order(TransactionType.Buy, self.symbol, self.lot)
            elif sell:
                self.api.place_order(TransactionType.Sell, self.symbol, self.lot)
        except Exception as e:
            print(f"Error placing order: {e}")

    def start_trading(self):
        """
        Start the trading bot.
        """
        self.initialize()
        timeframe_condition = self.verifier.get_verification_time(self.timeframe)

        while True:
            if datetime.now().strftime("%H:%M:%S") in timeframe_condition:
                print(datetime.now().strftime("%H:%M:%S"))

                buy, sell = self.strategy.create_signals(self.symbol, self.timeframe)
                res = self.get_open_positions()

                if ("symbol" in res.columns) and ("quantity" in res.columns):
                    if not (
                        (res["symbol"] == self.symbol) & (res["quantity"] == self.lot)
                    ).any():
                        self.run(buy, sell)
                else:
                    self.run(buy, sell)

                time.sleep(1)
