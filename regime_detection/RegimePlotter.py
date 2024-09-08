import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class RegimePlotter:
    def plot_hidden_states(self, hidden_states, prices_df, split_index=0):
        """
        Plot the hidden states and prices using matplotlib.

        Parameters:
        hidden_states (numpy.ndarray): Array of predicted hidden states.
        prices_df (pd.DataFrame): DataFrame of close prices.
        split_index (int): Index to split the data for training and testing.

        Raises:
        ValueError: If the input data is not valid or if the number of states exceeds the available colors.
        Exception: If an unexpected error occurs during plotting.
        """
        try:
            # Validate inputs
            if not isinstance(hidden_states, np.ndarray):
                raise ValueError("hidden_states must be a numpy ndarray.")
            if not isinstance(prices_df, pd.DataFrame):
                raise ValueError("prices_df must be a pandas DataFrame.")
            if split_index < 0 or split_index >= len(prices_df):
                raise ValueError("split_index is out of bounds.")

            # Slice the DataFrame to get the test portion
            test_prices_df = prices_df.iloc[split_index:].reset_index(drop=True)

            colors = [
                "blue",
                "green",
                "red",
            ]  # Adjust colors if more states are present
            n_components = len(np.unique(hidden_states))

            if n_components > len(colors):
                raise ValueError("Number of hidden states exceeds available colors.")

            plt.figure(figsize=(12, 6))

            for i in range(n_components):
                mask = hidden_states == i
                print(
                    "Number of observations for State ",
                    i,
                    ":",
                    len(test_prices_df.index[mask]),
                )

                plt.scatter(
                    test_prices_df.index[mask],
                    test_prices_df.iloc[mask, 0],
                    color=colors[i],
                    label="Hidden State " + str(i),
                    s=10,
                )

            plt.title("Hidden States and Prices")
            plt.xlabel("Date")
            plt.ylabel("Price")
            plt.legend()
            plt.tight_layout()
            plt.show()

        except ValueError as e:
            print(f"ValueError: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred during plotting: {e}")
            raise
