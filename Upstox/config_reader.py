import configparser


class ConfigReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.config = self._read_properties()

    def _read_properties(self):
        config = configparser.ConfigParser()
        config.read(self.file_path)
        return config["DEFAULT"]

    def get_property(self, key):
        return self.config.get(key)
