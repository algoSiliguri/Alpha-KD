import pandas as pd
import os
from ta.trend import CCIIndicator
from ta.volatility import AverageTrueRange
import DataPreprocessing as dp


class CCI_Flag:
    def __init__(
        self,
        input_dir,
        output_file,
        cci_window,
        atr_window,
        constant=0.015,
        atr_multiplier=1.5,
        take_profit=0.01,
    ):
        self.input_dir = input_dir
        self.output_file = output_file
        self.cci_window = cci_window
        self.atr_window = atr_window
        self.constant = constant
        self.atr_multiplier = atr_multiplier
        self.take_profit = take_profit

    def process_csv_files(self):
        for file_name in os.listdir(self.input_dir):
            if file_name.endswith(".csv"):
                file_path = os.path.join(self.input_dir, file_name)
                df = pd.read_csv(file_path)

                # Calculate CCI
                df = dp.cci(df, window=self.cci_window, constant=self.constant)

                # Calculate ATR
                df = dp.atr(df, self.atr_window)

                df.to_csv(file_path, index=False)

    def flag_stocks(self):
        flagged_stocks = []

        for file_name in os.listdir(self.input_dir):
            if file_name.endswith(".csv"):
                file_path = os.path.join(self.input_dir, file_name)
                df = pd.read_csv(file_path)

                # Logic to flag stocks for buying
                cci_current = df[f"CCI_{self.cci_window}"].iloc[-1]
                cci_previous = df[f"CCI_{self.cci_window}"].iloc[-2]
                last_day_close = df["close"].iloc[-1]

                # Update the trailing stop
                current_atr = df[f"ATR_{self.atr_window}"].iloc[-1]
                trailing_stop = last_day_close - self.atr_multiplier * current_atr

                # Check if CCI was below -100 and then crosses above -100
                if cci_previous < -100 < cci_current:
                    stock_name = file_name.replace("_day.csv", "")
                    flagged_stocks.append(
                        (stock_name, last_day_close, self.take_profit, trailing_stop)
                    )

        # After collecting flagged stocks
        if flagged_stocks:
            # Create a DataFrame from the list of flagged stocks with column headers
            result_df = pd.DataFrame(
                flagged_stocks,
                columns=[
                    "Stock Name",
                    "Last Day Close",
                    "Take Profit",
                    "Trailing Stop",
                ],
            )

            # Write the DataFrame to the output CSV file with the header
            result_df.to_csv(self.output_file, index=False)


# Example usage:
if __name__ == "__main__":
    input_dir = "../Upstox_Data/Fixed_Time_Bars"
    output_file = "../Upstox_Data/Buy_Flagged/CCI/flagged_stocks.csv"

    cci_flag = CCI_Flag(
        input_dir=input_dir,
        output_file=output_file,
        cci_window=15,
        atr_window=15,
        constant=0.015,
    )
    # cci_flag.process_csv_files()
    cci_flag.flag_stocks()
