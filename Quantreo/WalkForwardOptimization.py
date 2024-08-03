import itertools
import numpy as np
import pandas as pd
from tqdm import tqdm
from Quantreo.Backtest import Backtest


class WalkForwardOptimization:
    """
    A class for performing Walk-Forward Optimization on a trading strategy.

    This class is responsible for finding the optimal set of parameters for a
    trading strategy by dividing a dataset into multiple training and testing sets
    and running the strategy on each one.

    This method of optimization helps prevent curve fitting by ensuring that the
    strategy performs well over many different time periods and under various market conditions.

    Parameters
    ----------
    data: DataFrame
        The input data to be used for the backtests.

    TradingStrategy: object
        The trading strategy to be optimized.

    fixed_parameters: dict
        The parameters of the strategy that should remain fixed throughout the optimization process.

    parameters_range: dict
        The range of values that the non-fixed parameters of the strategy should take on during the optimization process.

    length_train_set: int, default 10_000
        The size of the training set in number of data points.

    pct_train_set: float, default .80
        The proportion of the dataset to be used for training.

    anchored: bool, default True
        Whether the training set should be anchored, meaning it always begins at the start of the dataset.
        If False, the training set will move forward in time with the test set.

    title: str, default None
        The title of the backtest's plot.

    randomness: float, default 0.75
        A factor to determine the size of the sample space for parameter combinations to be tested.

    """

    def __init__(
        self,
        data,
        TradingStrategy,
        fixed_parameters,
        parameters_range,
        length_train_set=10_000,
        pct_train_set=0.80,
        anchored=True,
        title=None,
        randomness=0.75,
    ):
        # Set initial parameters
        self.data = data
        self.TradingStrategy = TradingStrategy
        self.parameters_range = parameters_range
        self.fixed_parameters = fixed_parameters
        self.randomness = randomness
        self.dictionaries = None
        self.get_combinations()

        # Necessary variables to create our sub-samples
        self.length_train_set, self.pct_train_set = length_train_set, pct_train_set
        self.train_samples, self.test_samples, self.anchored = [], [], anchored

        # Necessary variables to compute and store our criteria
        self.BT, self.criterion = None, None
        self.best_params_sample_df, self.best_params_sample = None, None
        self.smooth_result = pd.DataFrame()
        self.best_params_smoothed = list()

        # Create dataframe that will contain the optimal parameters  (ranging parameters + criterion)
        self.columns = list(self.parameters_range.keys())
        self.columns.append("criterion")
        self.df_results = pd.DataFrame(columns=self.columns)

        # Set the title of our Backtest plot
        self.title_graph = title

    def get_combinations(self):
        """
        Generate all possible combinations of the non-fixed parameters and add the fixed parameters to each combination.

        This method creates a list of dictionaries where each dictionary represents a unique combination of parameter values
        to be tested during the optimization process. The fixed parameters are added to each combination.

        Raises
        ------
        ValueError
            If `parameters_range` is empty or not a dictionary.
        """
        # Validate parameters_range
        if not isinstance(self.parameters_range, dict) or not self.parameters_range:
            raise ValueError("parameters_range must be a non-empty dictionary")

        try:
            # Extract keys and generate combinations
            keys = list(self.parameters_range.keys())
            combinations = list(
                itertools.product(*[self.parameters_range[key] for key in keys])
            )

            # Create dictionaries for each combination and add fixed parameters
            self.dictionaries = [
                {**dict(zip(keys, combination)), **self.fixed_parameters}
                for combination in combinations
            ]
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while generating parameter combinations: {e}"
            )

    def run_optimization(self):
        """
        Execute the walk-forward optimization process.

        This method iterates through the training and testing sets, finds the best parameters for each training set,
        and then tests these parameters on the corresponding test set.

        Raises
        ------
        RuntimeError
            If an error occurs during the optimization process.
        """
        try:
            # Create the sub-samples
            self.get_sub_samples()

            # Run the optimization
            for self.train_sample, self.test_sample in tqdm(
                zip(self.train_samples, self.test_samples)
            ):
                self.get_best_params_train_set()
                self.test_best_params()
        except Exception as e:
            raise RuntimeError(
                f"An error occurred during the optimization process: {e}"
            )

    def get_sub_samples(self):
        """
        Split the dataset into multiple training and testing sets.

        This method divides the dataset into sub-samples based on the specified length of the training set,
        the proportion of the dataset to be used for training, and whether the training set should be anchored.

        Raises
        ------
        ValueError
            If the dataset is too small to create the specified number of sub-samples.
        """
        # Compute the length of the test set
        try:
            length_test = int(
                self.length_train_set / self.pct_train_set - self.length_train_set
            )
        except ZeroDivisionError:
            raise ValueError("pct_train_set must be greater than 0 and less than 1")

        if length_test <= 0:
            raise ValueError("The computed length of the test set must be positive")

        # Initialize size parameters
        start = 0
        end = self.length_train_set

        # Check if the dataset is large enough
        if len(self.data) <= end + 2 * length_test:
            raise ValueError(
                "The dataset is too small to create the specified number of sub-samples"
            )

        # Split the data until we can't make more than 2 sub-samples
        while (len(self.data) - end) > 2 * length_test:
            end += length_test

            # If we are at the last sample we take the whole rest to not create a tiny last sample
            if (len(self.data) - end) < 2 * length_test:
                if self.anchored:
                    self.train_samples.append(self.data.iloc[: end - length_test, :])
                    self.test_samples.append(
                        self.data.iloc[end - length_test : len(self.data), :]
                    )
                else:
                    self.train_samples.append(
                        self.data.iloc[start : end - length_test, :]
                    )
                    self.test_samples.append(
                        self.data.iloc[end - length_test : len(self.data), :]
                    )
                break

            # Fill the samples list depending on if there are anchored or not
            if self.anchored:
                self.train_samples.append(self.data.iloc[: end - length_test, :])
                self.test_samples.append(self.data.iloc[end - length_test : end, :])
            else:
                self.train_samples.append(self.data.iloc[start : end - length_test, :])
                self.test_samples.append(self.data.iloc[end - length_test : end, :])

            start += length_test

    def get_best_params_train_set(self):
        """
        Find the best set of parameters for the trading strategy based on the training set.

        This method evaluates different parameter combinations on the training set and selects the one
        that maximizes the performance criterion. The best parameters are stored for later testing on the test set.

        Raises
        ------
        RuntimeError
            If an error occurs during the criterion calculation or parameter selection.
        """
        try:
            # Store the possible parameter combinations with the associated criterion
            storage_values_params = []

            for self.params_item in np.random.choice(
                self.dictionaries,
                size=int(len(self.dictionaries) * self.randomness),
                replace=False,
            ):
                # Extract the variable parameters from the dictionary
                current_params = [
                    self.params_item[key] for key in list(self.parameters_range.keys())
                ]

                # Compute the criterion and add it to the list of params
                self.get_criterion(self.train_sample, self.params_item)
                current_params.append(self.criterion)

                # Add the current_params list to the storage_values_params in order to create a dataframe
                storage_values_params.append(current_params)

            df_find_params = pd.DataFrame(storage_values_params, columns=self.columns)

            # Extract the dataframe line with the best parameters
            self.best_params_sample_df = df_find_params.sort_values(
                by="criterion", ascending=False
            ).iloc[0:1, :]

            # Set the index for the best parameters
            self.best_params_sample_df.index = self.train_sample.index[-2:-1]

            # Add the best params to the dataframe which contains all the best params for each period
            self.df_results = pd.concat(
                (self.df_results, self.best_params_sample_df), axis=0
            )

            # Create a dictionary with the best params on the train set in order to test them on the test set later
            self.best_params_sample = dict(
                df_find_params.sort_values(by="criterion", ascending=False).iloc[0, :-1]
            )
            self.best_params_sample.update(self.fixed_parameters)
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while finding the best parameters: {e}"
            )

    def get_criterion(self, sample, params):
        """
        Calculate the performance criterion for a given sample and set of parameters.

        This method runs a backtest on the provided sample data with the specified parameters,
        computes the returns and maximum drawdown, and calculates a performance criterion.

        Parameters
        ----------
        sample : DataFrame
            The sample data to be used for the backtest.
        params : dict
            The parameters to be used for the trading strategy.

        Raises
        ------
        RuntimeError
            If an error occurs during the backtest or criterion calculation.
        """
        try:
            # Backtest initialization with a specific dataset and set of parameters
            self.BT = Backtest(
                data=sample, TradingStrategy=self.TradingStrategy, parameters=params
            )

            # Compute the returns of the strategy (on this specific dataset and with these parameters)
            self.BT.run()

            # Calculation and storage of the criterion (Return over period over the maximum drawdown)
            ret, dd = self.BT.metrics_display.get_ret_dd()

            # We add ret and dd because dd < 0
            self.criterion = ret + 2 * dd
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while calculating the criterion: {e}"
            )

    def get_smoother_result(self):
        """
        Smooth the results of the parameter optimization process to avoid overfitting.

        This method applies smoothing techniques to the results of the best parameters found during the training phase.
        It uses the exponential weighted mean for float columns and the mode for non-float columns.

        Returns
        -------
        dict
            A dictionary containing the smoothed parameters.

        Raises
        ------
        RuntimeError
            If an error occurs during the smoothing process.
        """
        try:
            self.smooth_result = pd.DataFrame()
            # For each column, we will extract the exp mean or the mode

            for column in self.df_results.columns:
                self.smooth_result[column] = (
                    self.df_results[column].ewm(com=1.5, ignore_na=True).mean()
                )

                """"
              Check on the extensiility of this piece of code 
              using different smoothening techniques isnce we are only using numeric value
              
              # # Check if the column contains numeric values (either float or integer)
              # if np.issubdtype(self.df_results[column].dtype, np.number):
              #     self.smooth_result[column] = (
              #         self.df_results[column].ewm(com=1.5, ignore_na=True).mean()
              #     )
              # else:
              #     self.smooth_result[column] = self.df_results[column].mode().iloc[0]
              
              
              """

            # Create a dictionary with the best params SMOOTHED by exponential mean or by the mode
            test_params = dict(self.smooth_result.iloc[-1, :-1])

            # New way to keep the ML algo weights in memory
            # We initialize the strategy class to train the weights if it is necessary
            Strategy = self.TradingStrategy(self.train_sample, self.best_params_sample)

            # Extract the output dictionary parameters
            output_params = Strategy.output_dictionary

            # Replace the ranging parameters by the smoothed parameters
            for key in test_params.keys():
                output_params[key] = test_params[key]

            return output_params
        except Exception as e:
            raise RuntimeError(f"An error occurred while smoothing the results: {e}")

    def test_best_params(self):
        """
        Test the best parameters found during the training phase on the test set.

        This method uses the smoothed parameters obtained from the get_smoother_result method
        and evaluates their performance on the test set. The criterion value in the results
        DataFrame is updated to reflect the performance on the test set.

        Raises
        ------
        RuntimeError
            If an error occurs during the criterion calculation or parameter testing.
        """
        try:
            # Extract smoothed best params
            smooth_best_params = self.get_smoother_result()

            # Compute the criterion on the test set, using the smoothed best params
            self.get_criterion(self.test_sample, smooth_best_params)

            # Update the criterion value in the results DataFrame
            self.df_results.at[self.df_results.index[-1], "criterion"] = self.criterion
            self.best_params_smoothed.append(smooth_best_params)
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while testing the best parameters: {e}"
            )

    def display(self):
        # Empty dataframe that will be filled by the result on each period
        df_test_result = pd.DataFrame()

        for params, test in zip(self.best_params_smoothed, self.test_samples):
            # !! Here, we can call directly the model without run again the model because the optimal weights are
            # computed already and stored into the output dictionary and so in the self.best_params_smoothed list
            self.BT = Backtest(
                data=test, TradingStrategy=self.TradingStrategy, parameters=params
            )
            self.BT.run()
            df_test_result = pd.concat((df_test_result, self.BT.data), axis=0)

        # Print the backtest for the period following the walk-forward method
        self.BT = Backtest(
            data=df_test_result, TradingStrategy=self.TradingStrategy, parameters=params
        )
        self.BT.display(self.title_graph)
