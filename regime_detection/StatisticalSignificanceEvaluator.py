import numpy as np
from scipy.stats import f_oneway, ttest_ind
import matplotlib.pyplot as plt
import seaborn as sns


class RegimeSignificanceEvaluator:
    def __init__(self, data, features):
        """
        Initialize the evaluator.

        :param data: The DataFrame containing the data with assigned regimes.
        :param features: List of features to evaluate for statistical significance and distinctiveness.
        """
        self.data = data
        self.features = features

    def evaluate_significance(self):
        """
        Evaluate the statistical significance of the regimes using ANOVA or t-tests.

        :return: A dictionary of p-values for each feature.
        """
        regimes = self.data["regime"].unique()
        results = {}

        for feature in self.features:
            regime_groups = [
                self.data[self.data["regime"] == regime][feature] for regime in regimes
            ]

            if len(regime_groups) > 2:
                # Use ANOVA for multiple regimes
                f_stat, p_value = f_oneway(*regime_groups)
            else:
                # Use t-test for two regimes
                f_stat, p_value = ttest_ind(regime_groups[0], regime_groups[1])

            results[feature] = p_value

        return results

    def plot_feature_distributions(self):
        """
        Plot the distributions of the features for each regime to visually inspect distinctiveness.
        """
        regimes = self.data["regime"].unique()

        for feature in self.features:
            plt.figure(figsize=(10, 6))
            for regime in regimes:
                sns.kdeplot(
                    self.data[self.data["regime"] == regime][feature],
                    label=f"Regime {regime}",
                )
            plt.title(f"Distribution of {feature} Across Regimes")
            plt.legend()
            plt.show()

    def evaluate_distinctiveness(self):
        """
        Evaluate how distinct the regimes are by visualizing the distributions of features.

        :return: None
        """
        self.plot_feature_distributions()
