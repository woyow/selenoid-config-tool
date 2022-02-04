from helpers.config_parser import ConfigParser
from icecream import ic


class Configurator:

    ic.enable()

    def __init__(self):
        self.config_parser = ConfigParser()
        self.config = self.config_parser()
        ic(self.config)

    def __call__(self):
        self.generate_result()

    def generate_result(self):
        print("Generate results")
        ic(len(self.config[0]))
