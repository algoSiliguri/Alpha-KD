

from LiveTradingStrategy.live_trading_strategy import TradingStrategy
from Quantreo.trading_bot import TradingBot
from Quantreo.timeframe_verifier import TimeframeVerifier
from Upstox.upstox_live_tradingAPI import UpstoxAPILive

import json
import math
import threading


if __name__ == "__main__":
    access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI4N0FIUzMiLCJqdGkiOiI2NmM1ODMxMzRkNWFhYjcyM2Q2NmY4YTIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzI0MjIwMTc5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3MjQyNzc2MDB9.z4cBanGk-kPuOcW-GUj0sAx_cKz67gLUiierc8jFazE'"
    symbol = "EURUSD-Z"

    # Open and read the tickers flagged
    with open('flagged_tickers.json', 'r') as file:
        flagged_tickers = json.load(file)

    previous_close_values = {"SAIL":300, "SBIN":134}

    for symbol,portfolio_weightage in flagged_tickers.get("cci")[0].items():

        # The api connection instance
        api = UpstoxAPILive(access_token)
        ltp = api.get_ltp(symbol)
        last_day_close = api.get_last_close(symbol)

        # Account balance
        account_balance = api.get_balance()

        # Getting the previous close data
        previous_close = last_day_close
        # previous_close = previous_close_values[symbol]

        # Strategy allocation balance multiplier
        strategy_allocation = flagged_tickers.get("cci")[1]

        # Final ticker allocation 
        ticker_allocation = strategy_allocation * portfolio_weightage

        # The qty for the ticker
        qty = math.ceil((ticker_allocation * account_balance)/ltp)

        timeframe = "8-hours"
        pct_tp = 0.0063
        pct_sl = 0.005

        # Starting the strategy
        strategy = TradingStrategy(previous_close)
        verifier = TimeframeVerifier()
        bot = TradingBot(api, strategy, verifier, symbol, qty, pct_tp, pct_sl, previous_close)
        threading.Thread(target=bot.start_trading).start()
