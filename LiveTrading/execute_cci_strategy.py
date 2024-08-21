import sys
import os
import threading

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from LiveTradingStrategy.live_trading_strategy import TradingStrategy
from Quantreo.trading_bot import TradingBot
from Quantreo.timeframe_verifier import TimeframeVerifier
from Upstox.upstox_live_tradingAPI import UpstoxAPILive

import json


if __name__ == "__main__":
    access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI4N0FIUzMiLCJqdGkiOiI2NmM1ODMxMzRkNWFhYjcyM2Q2NmY4YTIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzI0MjIwMTc5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3MjQyNzc2MDB9.z4cBanGk-kPuOcW-GUj0sAx_cKz67gLUiierc8jFazE'"
    symbol = "EURUSD-Z"

    # Open and read the tickers flagged
    with open('flagged_tickers.json', 'r') as file:
        flagged_tickers = json.load(file)

    previous_close_values = {"BEL":300, "SAIL":134}

    for symbol,portfolio_weightage in flagged_tickers.get("cci").items():
        print(symbol, portfolio_weightage)

        # Getting the previous close data
        previous_close = previous_close_values[symbol]

        timeframe = "8-hours"
        pct_tp = 0.0063
        pct_sl = 0.005

        api = UpstoxAPILive(access_token)
        strategy = TradingStrategy(previous_close)
        verifier = TimeframeVerifier()
        bot = TradingBot(api, strategy, verifier, symbol, portfolio_weightage, timeframe, pct_tp, pct_sl, previous_close)
        threading.Thread(target=bot.start_trading).start()
