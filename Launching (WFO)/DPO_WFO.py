import numpy as np
import pandas as pd
from Quantreo.WalkForwardOptimization import *
import warnings
from Strategies.DoubleEmaStrategy import DoubleEmaStrategy  # Assuming DpoStrategy is saved in Strategies folder
from Strategies.DpoStrategy import DpoStrategy

warnings.filterwarnings("ignore")

# Load the dataset
df = pd.read_csv(
    "../Upstox_Data/Create_Database/Nifty50_data/Daily/WIPRO_Daily.csv",
    index_col="time",
    parse_dates=True,
)

# Define the range of values for each parameter
params_range = {
    "dpo_period": range(21, 23),  # Example range from 14 to 16
    # "long_ema_period":  range(21,23),
    "atr_period": range(10, 16),  # Example range from 10 to 16
}

# Define the fixed value for the cost parameter
params_fixed = {"cost": 10, "atr_multiplier": 1.5, "atr_period": 14}

# Calculate the length of the training set as 35% of the total dataset length
length_train_set = int(len(df) * 0.35)

# Initialize the WalkForwardOptimization class
WFO = WalkForwardOptimization(
    data=df,
    TradingStrategy=DpoStrategy,
    fixed_parameters=params_fixed,
    parameters_range=params_range,
    length_train_set=length_train_set,  # Training set size as 35% of the dataset
    pct_train_set=0.70,  # 70% of the data for training
    anchored=True,  # Use anchored training sets
    title="Walk-Forward Optimization",
    randomness=1.00,  # Test all parameter combinations
)

# Run the optimization
WFO.run_optimization()

# Extract best parameters
params = WFO.best_params_smoothed[-1]
print("BEST PARAMETERS")
print(params)

# Show the results
WFO.display()