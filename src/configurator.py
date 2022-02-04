from helpers.config_parser import ConfigParser


class Configurator:

    def __init__(self):
        self.config = ConfigParser()
        print(self.config)

    def __call__(self):
        print("CALL CONFIGURATOR")
        self.config()
        self.generate_result()

    def generate_result(self):
        print("Generate results")
