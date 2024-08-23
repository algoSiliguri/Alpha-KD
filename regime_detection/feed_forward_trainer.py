import numpy as np
import math


class FeedForwardTrainer:
    def __init__(self, regime_detector, retrain_step):
        """
        Initialize the FeedForwardTrainer with a regime detector and retrain step.

        Parameters:
        regime_detector: An object that has a method `detect_regime` for detecting regimes.
        retrain_step (int): The number of steps after which the model should be retrained.
        """
        self.regime_detector = regime_detector
        self.retrain_step = retrain_step

    def train_and_predict(self, df, split_index):
        """
        Train the model on initial data and predict states for the test data.

        Parameters:
        df (pd.DataFrame): DataFrame containing the data for training and prediction.
        split_index (int): The index at which to split the data into training and test sets.

        Returns:
        np.ndarray: An array of predicted states.

        Raises:
        KeyError: If the required features are not present in the DataFrame.
        ValueError: If the split_index is out of bounds or if the DataFrame is empty.
        """
        try:
            # Initial training
            if split_index <= 0 or split_index >= len(df):
                raise ValueError("split_index is out of bounds.")

            init_train_data = df.iloc[:split_index]
            test_data = df.iloc[split_index:]
            rd_model = self.regime_detector.detect_regime(init_train_data)

            states_pred = []
            for i in range(math.ceil(len(test_data))):
                split_index += 1

                # Extract the feature array for prediction
                feature_data = df.iloc[:split_index][
                    self.regime_detector.params["features"]
                ].values

                preds = rd_model.predict(feature_data).tolist()
                states_pred.append(preds[-1])

                if i % self.retrain_step == 0:
                    # Retrain the model with updated data
                    rd_model = self.regime_detector.detect_regime(df.iloc[:split_index])

            return np.array(states_pred)

        except KeyError as e:
            print(f"KeyError: {e}")
            raise
        except ValueError as e:
            print(f"ValueError: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
