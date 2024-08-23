from regime_detection import RegimeDetection
import pandas as pd

from RegimePlotter import RegimePlotter
from feature_engineering import FeatureEngineering
from feed_forward_trainer import FeedForwardTrainer

# Example usage
filepath = "../Upstox_Data/Fixed_Time_Bars/NIFTYBEES_day.csv"
data = pd.read_csv(filepath)


# Initialize the FeatureEngineering class
feature_engineer = FeatureEngineering()

# Calculate the log return of the moving average
data = feature_engineer.calculate_log_return_of_moving_average(data)

# Normalize the log return
data = feature_engineer.normalize_data(data, "log_return")


# Initialize and use the RegimeDetection class
params = {"n_components": 2, "features": ["log_return"]}

# Prepare data for HMM
log_return_data = data["log_return"].values.reshape(-1, 1)

# Initialize the RegimeDetection
regime_detector = RegimeDetection("hmm", params)

# Initialize the FeedForwardTrainer
trainer = FeedForwardTrainer(regime_detector, retrain_step=20)

# Train and predict
split_index = int(len(log_return_data) * 0.3)
states_pred = trainer.train_and_predict(data, split_index)


## For in-sample testing
# regime_detector = RegimeDetection("hmm", params)
# hmm_model = regime_detector.detect_regime(data, params)
#
# # Use the fitted model to predict the hidden states for the in-sample data
# log_return_data = data["log_return"].values.reshape(-1, 1)  # Reshape for HMM input
# predicted_states = hmm_model.predict(log_return_data)


# Initialize the Plotter class and plot the hidden states
plotter = RegimePlotter()
plotter.plot_hidden_states(states_pred, data[["close"]], split_index)
