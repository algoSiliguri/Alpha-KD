from Strategies.ZScore_Mean_Reversion import MeanReversionStrategy
from Quantreo.WalkForwardOptimization import *
import warnings
import pandas as pd

warnings.filterwarnings("ignore")

# Load the dataset
df = pd.read_csv(
    "../Upstox_Data/Create_Database/Nifty50_data/Daily/HINDUNILVR_Daily.csv",
    index_col="time",
    parse_dates=True,
)

# Define the range of values for each parameter
params_range = {"zscore_threshold": np.arange(-3, -1.4, 0.1).tolist()}

# Define the fixed value for the cost parameter
params_fixed = {
    "cost": 10,
    "atr_multiplier": 1.75,
    "atr_period": 14,
    "zscore_period": 21,
}

# Calculate the length of the training set as 35% of the total dataset length
length_train_set = int(len(df) * 0.35)

# Initialize the WalkForwardOptimization class
WFO = WalkForwardOptimization(
    data=df,
    TradingStrategy=MeanReversionStrategy,
    fixed_parameters=params_fixed,
    parameters_range=params_range,
    length_train_set=length_train_set,  # Training set size as 70% of the dataset
    pct_train_set=0.70,  # 70% of the data for training
    anchored=False,  # Use anchored training sets
    title="Walk-Forward Optimization",
    randomness=0.6,  # Test all parameter combinations
)

# Run the optimization
WFO.run_optimization()

# Extract best parameters
params = WFO.best_params_smoothed[-1]
print("BEST PARAMETERS")
print(params)

# Show the results
WFO.display()
