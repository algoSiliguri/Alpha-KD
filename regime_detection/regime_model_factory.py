from markov_switching_model import MarkovSwitchingModel
from hidden_markov_model import HiddenMarkovModel


class RegimeModelFactory:
    @staticmethod
    def create_model(model_type, params):
        """
        Create a regime model based on the specified type.

        Parameters:
        model_type (str): The type of model to create ('markov' or 'hmm').
        params (dict): A dictionary containing parameters for the model.

        Returns:
        An instance of the specified model type.

        Raises:
        ValueError: If an unsupported model type is provided.
        Exception: If an error occurs during model creation.
        """
        try:
            if model_type == "markov":
                return MarkovSwitchingModel(params)
            elif model_type == "hmm":
                return HiddenMarkovModel(params)
            else:
                raise ValueError("Unsupported model type. Choose 'markov' or 'hmm'.")
        except ValueError as e:
            print(f"ValueError: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred during model creation: {e}")
            raise
