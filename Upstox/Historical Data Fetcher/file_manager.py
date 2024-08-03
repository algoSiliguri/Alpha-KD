import os
import pandas as pd


class FileManager:
    """
    FileManager is responsible for handling file operations such as ensuring directories exist and writing data to CSV files.
    """

    @staticmethod
    def ensure_directory_exists(directory: str):
        """
        Ensures that the specified directory exists. If it does not exist, it creates the directory.

        Args:
            directory (str): The path of the directory to check or create.

        Raises:
            OSError: If there is an error creating the directory.
        """
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            raise

    @staticmethod
    def write_to_csv(data_frame: pd.DataFrame, output_file: str):
        """
        Writes the given DataFrame to a CSV file at the specified path.

        Args:
            data_frame (pd.DataFrame): The DataFrame to write to CSV.
            output_file (str): The path of the output CSV file.

        Raises:
            IOError: If there is an error writing the DataFrame to the CSV file.
        """
        try:
            data_frame.to_csv(output_file)
        except IOError as e:
            print(f"Error writing to CSV file {output_file}: {e}")
            raise
