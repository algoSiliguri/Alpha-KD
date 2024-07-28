from Quantreo.LiveTradingSignal import CciStrategy


def main():
    symbol = "EURUSD"
    timeframe = "M5"
    cci_period = 20
    atr_period = 14
    atr_multiplier = 3
    cost = 0.0001  # Example transaction cost

    trailing_stop = None
    open_buy_price = None
    open_sell_price = None
    entry_time = None
    exit_time = None
    buy_position_open = False
    sell_position_open = False

    while True:
        try:
            buy_signal, sell_signal, df, current_price, atr_value = (
                CciStrategy(
                    symbol, timeframe, cci_period, atr_period, atr_multiplier
                )
            )

            if buy_signal and not buy_position_open:
                place_order(symbol, "buy")
                open_buy_price = df["open"].iloc[-1]
                entry_time = df.index[-1]
                trailing_stop = open_buy_price - atr_multiplier * atr_value
                buy_position_open = True
                print(f"Placed a buy order for {symbol} at {open_buy_price}")

            if sell_signal and not sell_position_open:
                place_order(symbol, "sell")
                open_sell_price = df["open"].iloc[-1]
                entry_time = df.index[-1]
                trailing_stop = open_sell_price + atr_multiplier * atr_value
                sell_position_open = True
                print(f"Placed a sell order for {symbol} at {open_sell_price}")

            if buy_position_open:
                # Update trailing stop for buy position
                new_trailing_stop = current_price - atr_multiplier * atr_value
                if new_trailing_stop > trailing_stop:
                    trailing_stop = new_trailing_stop

                # Check for exit signal based on trailing stop
                if current_price < trailing_stop:
                    close_position(symbol, "buy")
                    exit_time = df.index[-1]
                    profit_loss = (
                        current_price - open_buy_price - cost
                    ) / open_buy_price
                    buy_position_open = False
                    print(
                        f"Closed buy position for {symbol} at {current_price} with P/L: {profit_loss}"
                    )

            if sell_position_open:
                # Update trailing stop for sell position
                new_trailing_stop = current_price + atr_multiplier * atr_value
                if new_trailing_stop < trailing_stop:
                    trailing_stop = new_trailing_stop

                # Check for exit signal based on trailing stop
                if current_price > trailing_stop:
                    close_position(symbol, "sell")
                    exit_time = df.index[-1]
                    profit_loss = (
                        open_sell_price - current_price - cost
                    ) / open_sell_price
                    sell_position_open = False
                    print(
                        f"Closed sell position for {symbol} at {current_price} with P/L: {profit_loss}"
                    )

            time.sleep(60)  # Wait for a minute before checking again

        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
