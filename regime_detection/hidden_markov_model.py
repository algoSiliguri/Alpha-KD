import warnings
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from regime_model import RegimeModel


class HiddenMarkovModel(RegimeModel):
    def __init__(self, params):
        """
        Initialize the HiddenMarkovModel with specified parameters.

        Parameters:
        params (dict): A dictionary containing parameters for the GaussianHMM model.
        """
        # Suppress specific warnings related to attribute overwriting
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            self.model = GaussianHMM(
                n_components=params.get("n_components", 2),
                covariance_type=params.get("covariance_type", "full"),
                n_iter=params.get("n_iter", 100),
                random_state=params.get("random_state", 100),
                init_params="",
            )

    def fit(self, df, params):
        """
        Fit the Hidden Markov Model to the data.

        Parameters:
        df (pd.DataFrame): DataFrame containing the data to fit the model.
        params (dict): A dictionary containing parameters, including 'features' to specify the columns to use.

        Returns:
        GaussianHMM: The fitted GaussianHMM model.

        Raises:
        ValueError: If the input data is not a pandas DataFrame or if the specified features are not present.
        """
        try:
            # Ensure df is a DataFrame and access the correct column
            if not isinstance(df, pd.DataFrame):
                raise ValueError("Input data must be a pandas DataFrame.")

            features = params.get("features")
            if features is None or not all(
                feature in df.columns for feature in features
            ):
                raise ValueError("Specified features are not present in the DataFrame.")

            data = df[features].values
            self.model.fit(data)
            return self.model

        except ValueError as e:
            print(f"ValueError: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise

    def num_params(self):
        """
        Calculate the number of parameters in the model.

        This method computes the total number of parameters required for the model,
        including transition probabilities, emission means and covariances, and initial
        state probabilities.

        Returns:
            int: The total number of parameters in the model.

        Raises:
            AttributeError: If the model does not have the attribute `n_components`.
            TypeError: If `n_components` is not an integer.
        """
        try:
            n_components = self.model.n_components
            if not isinstance(n_components, int):
                raise TypeError("n_components must be an integer.")

            # Transition probabilities + emission means and covariances + initial state probabilities
            num_params = (
                n_components * (n_components - 1)
                + 2 * n_components
                + (n_components - 1)
            )
            return num_params
        except AttributeError as e:
            raise AttributeError(
                "The model does not have the attribute 'n_components'."
            ) from e
        except TypeError as e:
            raise TypeError("n_components must be an integer.") from e
