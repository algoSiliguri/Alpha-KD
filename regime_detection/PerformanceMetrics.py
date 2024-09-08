import numpy as np


class PerformanceMetrics:
    """Handles the calculation of log-likelihood, AIC, and BIC."""

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
