from LiveTradingStrategy.live_trading_strategy import TradingStrategy
from Quantreo.trading_bot import TradingBot
from Quantreo.timeframe_verifier import TimeframeVerifier
from Upstox.upstox_live_tradingAPI import UpstoxAPILive

if __name__ == "__main__":
    api_key = "your_api_key"
    access_token = "your_access_token"
    symbol = "EURUSD-Z"
    lot = 0.1
    timeframe = "8-hours"
    pct_tp = 0.0063
    pct_sl = 0.005

    api = UpstoxAPILive(access_token)
    strategy = TradingStrategy()
    verifier = TimeframeVerifier()
    # symbol, lot would come from some csv

    bot = TradingBot(api, strategy, verifier, symbol, lot, timeframe, pct_tp, pct_sl)
    bot.start_trading()
