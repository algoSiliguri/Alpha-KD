import numpy as np


class AdaptiveFeedForwardTrainer:
    def __init__(self, regime_detector, window_size=10, adaptive=True):
        """
        Initialize the trainer.

        :param regime_detector: The HMM model used for regime detection.
        :param window_size: The rolling window size to calculate performance metrics.
        :param adaptive: Whether to adaptively adjust the retraining step.
        """
        self.regime_detector = regime_detector
        self.window_size = window_size
        self.adaptive = adaptive
        self.log_likelihoods = []  # To track log-likelihood over the rolling window
        self.aic_scores = []  # To track AIC over the rolling window
        self.bic_scores = []  # To track BIC over the rolling window

    def calculate_aic_bic(self, log_likelihood, num_params, num_data_points):
        """
        Calculate AIC and BIC for the model based on log-likelihood.

        :param log_likelihood: The log-likelihood of the model on recent data.
        :param num_params: The number of parameters in the model.
        :param num_data_points: The number of data points in the recent window.
        :return: AIC and BIC scores.
        """
        aic = 2 * num_params - 2 * log_likelihood
        bic = np.log(num_data_points) * num_params - 2 * log_likelihood
        return aic, bic

    def check_for_retraining(self):
        """
        Check if retraining is needed based on performance metrics.

        :return: Boolean indicating if retraining is needed.
        """
        if len(self.log_likelihoods) >= self.window_size:
            # Compute rolling mean and standard deviation of log-likelihood, AIC, and BIC
            log_likelihood_mean = np.mean(self.log_likelihoods[-self.window_size :])
            log_likelihood_std = np.std(self.log_likelihoods[-self.window_size :])
            aic_mean = np.mean(self.aic_scores[-self.window_size :])
            aic_std = np.std(self.aic_scores[-self.window_size :])
            bic_mean = np.mean(self.bic_scores[-self.window_size :])
            bic_std = np.std(self.bic_scores[-self.window_size :])

            # Calculate z-scores for the latest metrics
            z_log_likelihood = (
                self.log_likelihoods[-1] - log_likelihood_mean
            ) / log_likelihood_std
            z_aic = (self.aic_scores[-1] - aic_mean) / aic_std
            z_bic = (self.bic_scores[-1] - bic_mean) / bic_std

            # Trigger retraining if any z-score indicates significant degradation
            if z_log_likelihood < -2 or z_aic > 2 or z_bic > 2:
                return True

        return False

    def train_and_predict(self, df, split_index):
        """
        Train the model and make predictions using adaptive retraining.

        :param df: The input data (pandas DataFrame).
        :param split_index: The index at which the data is split into training and testing sets.
        :return: The predicted states.
        """
        # Initial training
        init_train_data = df.iloc[:split_index]
        rd_model = self.regime_detector.detect_regime(init_train_data)

        states_pred = []

        for i in range(len(df) - split_index):
            current_index = split_index + i

            # Extract the feature array for prediction
            feature_data = df.iloc[: current_index + 1][
                self.regime_detector.params["features"]
            ].values
            preds = rd_model.predict(feature_data).tolist()
            states_pred.append(preds[-1])

            # Calculate log-likelihood for the current prediction
            log_likelihood = rd_model.score(feature_data)
            self.log_likelihoods.append(log_likelihood)

            # Calculate AIC and BIC based on log-likelihood
            num_params = self.regime_detector.model.num_params()
            aic, bic = self.calculate_aic_bic(
                log_likelihood, num_params, len(feature_data)
            )
            self.aic_scores.append(aic)
            self.bic_scores.append(bic)

            # Adaptively retrain the model based on performance
            if self.adaptive and self.check_for_retraining():
                print(
                    f"Retraining model at index {current_index} due to performance deterioration."
                )
                rd_model = self.regime_detector.detect_regime(
                    df.iloc[: current_index + 1]
                )

        return np.array(states_pred)
