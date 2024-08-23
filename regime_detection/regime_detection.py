from regime_model_factory import RegimeModelFactory


class RegimeDetection:
    def __init__(self, model_type, params):
        """
        Initialize the RegimeDetection with a specified model type and parameters.

        Parameters:
        model_type (str): The type of model to create.
        params (dict): A dictionary containing parameters for the model.
        """
        try:
            self.model = RegimeModelFactory.create_model(model_type, params)
            self.params = params
        except Exception as e:
            print(f"An error occurred while creating the model: {e}")
            raise

    def detect_regime(self, df):
        """
        Detect the regime using the specified model.

        Parameters:
        df (pd.DataFrame): DataFrame containing the data for regime detection.

        Returns:
        The fitted model after detecting the regime.

        Raises:
        Exception: If an error occurs during model fitting.
        """
        try:
            return self.model.fit(df, self.params)
        except Exception as e:
            print(f"An error occurred during regime detection: {e}")
            raise
