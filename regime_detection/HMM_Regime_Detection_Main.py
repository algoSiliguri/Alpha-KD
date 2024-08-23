from regime_detection import RegimeDetection
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Example usage
filepath = "../Upstox_Data/Fixed_Time_Bars/NIFTYBEES_day.csv"
data = pd.read_csv(filepath)


def calculate_log_return_of_moving_average(df, window=7):
    """
    Calculate the log return of the moving average of historical close prices and drop NaN values.

    Parameters:
    df (pd.DataFrame): DataFrame containing the historical data with a 'close' column.
    window (int): The window size for the moving average. Default is 7.

    Returns:
    pd.DataFrame: A pandas DataFrame containing the log returns of the moving average with NaN values dropped.
    """
    # Calculate the moving average of the 'close' prices
    df["moving_avg"] = df["close"].rolling(window=window).mean()

    # Calculate the log returns of the moving average
    df["log_return"] = np.log(df["moving_avg"] / df["moving_avg"].shift(1))

    # Drop NaN values
    df.dropna(inplace=True)

    return df


def plot_hidden_states_matplotlib(hidden_states, prices_df):
    """
    Input:
    hidden_states(numpy.ndarray) - array of predicted hidden states
    prices_df(df) - dataframe of close prices

    Output:
    Graph showing hidden states and prices using matplotlib
    """

    colors = ["blue", "green", "red"]  # Adjust colors if more states are present
    n_components = len(np.unique(hidden_states))

    plt.figure(figsize=(12, 6))

    for i in range(n_components):
        mask = hidden_states == i
        print("Number of observations for State ", i, ":", len(prices_df.index[mask]))

        plt.scatter(
            prices_df.index[mask],
            prices_df.iloc[mask, 0],
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


data = calculate_log_return_of_moving_average(data)


# Initialize and use the RegimeDetection class
params = {"n_components": 3, "features": ["log_return"]}
regime_detector = RegimeDetection("hmm", params)
hmm_model = regime_detector.detect_regime(data, params)

# Use the fitted model to predict the hidden states for the in-sample data
log_return_data = data["log_return"].values.reshape(-1, 1)  # Reshape for HMM input
predicted_states = hmm_model.predict(log_return_data)


# Plot the hidden states with the close prices
plot_hidden_states_matplotlib(predicted_states, data[["close"]])
